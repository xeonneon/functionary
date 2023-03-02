import io
import json
import logging
import os
import shutil
import tarfile
from typing import List, Union
from uuid import UUID

import docker
import yaml
from celery.utils.log import get_task_logger
from django.conf import settings
from django.db import transaction
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from docker import DockerClient
from docker.errors import APIError, BuildError, DockerException
from docker.models.images import Image

from core.models import Environment, Function, FunctionParameter, Package, User

from .celery import app
from .exceptions import InvalidPackage
from .models import Build, BuildLog, BuildResource

logger = get_task_logger(__name__)
logger.setLevel(getattr(logging, settings.LOG_LEVEL))


class DockerSocketConnectionError(Exception):
    pass


def extract_package_definition(package_contents: bytes) -> dict:
    """Extracts the package.yaml from a package tarball

    Args:
        package_contents: gzipped tarball of a package

    Returns:
        The package definition yaml loaded as a dict
    """
    package_contents_io = io.BytesIO(package_contents)

    try:
        tarball = tarfile.open(fileobj=package_contents_io, mode="r")
    except tarfile.ReadError:
        raise InvalidPackage(
            "Could not untar package file. Make sure it is a valid gzipped tarball."
        )

    def close_files():
        package_contents_io.close()
        tarball.close()

    try:
        package_definition_io = tarball.extractfile("package.yaml")
    except KeyError:
        close_files()
        raise InvalidPackage("package.yaml not found")

    if package_definition_io is None:
        close_files()
        raise InvalidPackage("package.yaml found, but is not a regular file")

    package_definition = yaml.safe_load(package_definition_io.read())
    close_files()

    return package_definition


def initiate_build(
    creator: User,
    environment: Environment,
    package_contents: bytes,
    package_definition: dict,
    package_definition_version: str,
) -> Build:
    """Creates the Build and BuildResource instances necessary to initiate a build and
    then creates the task for the worker that will perform the build.

    Args:
        creator: The User initiating the build
        environment: The environment that the package should be published under
        package_contents: A gzipped file containing the package to be built
        package_definition: dict containing the package definition
    """
    with transaction.atomic():
        package_obj = None

        try:
            package_obj = Package.objects.get(
                environment=environment, name=package_definition.get("name")
            )
        except Package.DoesNotExist:
            pass

        build = Build.objects.create(
            creator=creator, environment=environment, package=package_obj
        )

        BuildResource(
            build=build,
            package_contents=package_contents,
            package_definition=package_definition,
            package_definition_version=package_definition_version,
        ).save()

    build_package.delay(build_id=build.id)

    return build


def _format_build_results(build_results):
    """
    Helper function for build_package to format build results
    as a more readable string

    Args:
        build_results: iterator returned from docker build
    Returns:
        string representation of build log

    """
    log = ""

    for line in build_results:
        line_str = ""

        for value in line.values():
            line_str += str(value)

        log += line_str

    return log


def _format_push_results(push_results):
    """
    Helper function for build_package to format push results
    as a more readable string

    Args:
        push_results: generator object created from docker push
    Returns:
        string representation of the push log
    """
    log = ""

    for line in push_results:
        dict_line = json.loads(line.decode("utf-8"))
        if status := dict_line.get("status"):
            if id := dict_line.get("id"):
                line_str = f"{id}: {status}"
            else:
                line_str = status

            log += line_str + "\n"

    return log


@app.task
def build_package(build_id: UUID):
    """Retrieve the resources for Build and use them to build and push the package
    docker image. Also creates BuildLog with build/push information.

    Args:
        build_id: ID of the build being executed
    """
    build = Build.objects.select_related("environment").get(id=build_id)

    try:
        build, build_log = _build_package(build)
        BuildLog.objects.create(build=build, log=build_log)
        _update_build_status(build)
    except DockerSocketConnectionError as err:
        logger.fatal(f"Unable to build image. {err}")
    except Exception as err:
        logger.error(f"Build encountered unexpected error: {err}")
        build.status = Build.ERROR
        BuildLog.objects.create(build=build, log=str(err))
        _update_build_status(build)


def _extract_package_contents(
    package_contents: bytes, workdir: str
) -> Union[None, str]:
    """Extracts the contents of the package tarball

    Args:
        package_contents: The package file bytes
        workdir: The directory to export the package contents to

    Returns:
        None: If successful extraction, nothing will be returned.
        err_msg: If an error is encountered, the error string will be returned
            for the build log.
    """
    package_contents_io = io.BytesIO(package_contents)
    try:
        tarball = tarfile.open(fileobj=package_contents_io, mode="r")
        tarball.extractall(workdir)
    except tarfile.ReadError as err:
        err_msg = f"Failed to read tarfile: {err}"
        logger.error(err_msg)
        return err_msg
    except Exception as err:
        err_msg = f"Failed extracting package contents: {err}"
        logger.error(err_msg)
        return err_msg
    finally:
        tarball.close()
        package_contents_io.close()


def _load_dockerfile_template(
    dockerfile_template: str, workdir: str
) -> Union[None, str]:
    """Render the dockfile template and write it to the working directory

    Args:
        dockerfile_template: The dockerfile template to load and render
        worder: The work directory path to render the dockerfile into

    Returns:
        None: Returns None if loading and rendering the dockerfile is successful
        err_msg: A string containing the error message if unsuccessful
    """
    try:
        template = get_template(dockerfile_template)
    except TemplateDoesNotExist:
        err_msg = "Template does not exist."
        logger.error(err_msg)
        return err_msg

    context = {"registry": settings.REGISTRY}

    with open(f"{workdir}/Dockerfile", "w") as dockerfile:
        dockerfile.write(template.render(context=context))


def _create_package_from_definition(
    package_definition: dict, environment: Environment
) -> Package:
    """Create a package from definitions"""
    # TODO: Manually parsing for now, but this should be codified somewhere, with
    #       the parsing informed by package_definition_version.
    name = package_definition.get("name")

    try:
        package_obj = Package.objects.get(environment=environment, name=name)
    except Package.DoesNotExist:
        package_obj = Package(
            environment=environment,
            name=name,
        )

    package_obj.display_name = package_definition.get("display_name")
    package_obj.summary = package_definition.get("summary")
    package_obj.description = package_definition.get("description")
    package_obj.language = package_definition.get("language")

    package_obj.save()

    return package_obj


def _create_parameters_from_definition(
    function_definition: dict, function: Function
) -> List[FunctionParameter]:
    """Creates the FunctionParameter objects for the provided function based on the
    function_definition"""
    parameters = []
    parameter_defs: list[dict] = function_definition.get("parameters", [])

    for parameter in parameter_defs:
        try:
            function_parameter = FunctionParameter.objects.get(
                function=function, name=parameter.get("name")
            )
        except FunctionParameter.DoesNotExist:
            function_parameter = FunctionParameter(
                function=function, name=parameter.get("name")
            )

        function_parameter.description = parameter.get("description")
        function_parameter.parameter_type = parameter.get("type")
        function_parameter.default = parameter.get("default")
        function_parameter.required = parameter.get("required")

        parameters.append(function_parameter)

    return parameters


def _create_functions_from_definition(definitions: list[dict], package: Package):
    """Creates the functions in the package from the definition file"""
    functions = []
    function_parameters = []

    for function_def in definitions:
        name = function_def.get("name")
        try:
            function_obj = Function.objects.get(package=package, name=name)
        except Function.DoesNotExist:
            function_obj = Function(
                package=package, name=name, environment=package.environment
            )

        function_obj.display_name = function_def.get("display_name")
        function_obj.summary = function_def.get("summary")
        function_obj.return_type = function_def.get("return_type")
        function_obj.description = function_def.get("description")
        function_obj.variables = function_def.get("variables", [])
        function_obj.active = True

        functions.append(function_obj)
        function_parameters.extend(
            _create_parameters_from_definition(function_def, function_obj)
        )

    return functions, function_parameters


def _deactivate_removed_functions(definitions, package: Package):
    """Deactivate and package functions not present in the definitions"""
    function_names = []

    for function_def in definitions:
        function_names.append(function_def.get("name"))

    removed_functions = Function.objects.filter(package=package).exclude(
        name__in=function_names
    )

    for function in removed_functions:
        function.deactivate()


def _delete_removed_function_parameters(
    function_parameters: List[FunctionParameter], package: Package
) -> None:
    """Deletes any FunctionParameters that are not in the provided function_parameters
    for the supplied package
    """
    ids_to_keep = [parameter.id for parameter in function_parameters]

    FunctionParameter.objects.filter(function__package=package).exclude(
        id__in=ids_to_keep
    ).delete()


def _build_package(build: Build) -> tuple[Build, str]:
    """Generate and build necessary resources to complete image build

    Args:
        build: The build object containing metadata about the build

    Returns:
        build: The build object with updated attribute values
        build_log: The log string of the entire build process

    Raises:
        DockerSockerConnectionError: Raised when connection to the docker socket
        could not be established.
    """
    build_log = ""
    build_id = build.id

    docker_client = _get_docker_client()

    logger.info(f"Starting build {build_id}")

    workdir = f"{settings.BUILDER_WORKDIR_BASE}/{build_id}"
    os.makedirs(workdir)

    build.status = Build.IN_PROGRESS
    _update_build_status(build)

    (
        package,
        image_name,
        full_image_name,
        dockerfile,
        package_contents,
        functions,
        function_parameters,
        function_definitions,
    ) = _create_build_resources(build)

    err_msg, build.status = _prepare_image_build(dockerfile, package_contents, workdir)

    if build.status == Build.ERROR:
        build_log = _update_log(build_log, err_msg)
        return build, build_log

    image, build_results, build.status = _build_image(
        docker_client, full_image_name, workdir
    )
    build_log = _update_log(build_log, build_results)

    if build.status == Build.ERROR:
        return build, build_log

    push_results, build.status = _push_image(docker_client, full_image_name)
    build_log = _update_log(build_log, push_results)

    if build.status != Build.COMPLETE:
        return build, build_log

    with transaction.atomic():
        _save_functions(functions, function_parameters)
        _delete_removed_functions(function_definitions, function_parameters, package)
        package.image_name = image_name
        package.save()

    _cleanup(docker_client, image, workdir, build_id)

    logger.info(f"Build {build_id} COMPLETE")
    return build, build_log


def _prepare_image_build(
    dockerfile: str, package_contents: bytes, workdir: str
) -> tuple[str, str]:
    """Generates artifacts necessary for building the new image

    Args:
        dockerfile: The dockerfile string containing the image details
        package_contents: The bytes that makeup the package contents
        workdir: The directory to dump the artifacts into

    Returns:
        err_log: The log of error messages encountered in generating
            the image artifacts.
        status: The build status of the image build preparation step. Is either
            `IN_PROGRESS` or `ERROR`.
    """
    err_log = ""
    status = Build.IN_PROGRESS

    if err_msg := _extract_package_contents(package_contents, workdir):
        err_log = _update_log(err_log, err_msg)
        status = Build.ERROR

    if err_msg := _load_dockerfile_template(dockerfile, workdir):
        err_log = _update_log(err_log, err_msg)
        status = Build.ERROR

    return err_log, status


def _create_build_resources(
    build: Build,
) -> tuple[
    Package, str, str, str, bytes, list[Function], list[FunctionParameter], list[dict]
]:
    environment = build.environment
    package = build.package
    package_contents = build.resources.package_contents
    package_definition = build.resources.package_definition
    function_definitions = package_definition.get("functions")

    image_name, dockerfile = build.resources.image_details
    full_image_name = f"{settings.REGISTRY}/{image_name}"

    if not package:
        with transaction.atomic():
            package = _create_package_from_definition(package_definition, environment)
            build.package = package
            build.save()

    # Need to validate the potentially new function schema, but
    # don't save it until the build has finished.
    functions, function_parameters = _create_functions_from_definition(
        function_definitions, package
    )

    return (
        package,
        image_name,
        full_image_name,
        dockerfile,
        package_contents,
        functions,
        function_parameters,
        function_definitions,
    )


def _build_image(
    docker_client: DockerClient, full_image_name: str, workdir: str
) -> tuple[Union[Image, None], str, str]:
    """Build a new image with the given image name

    Args:
        docker_client: The DockerClient used to interface with the Docker socket
        full_image_name: The image name, including the tag
        workdir: The directory that contains the artifacts necessary to build
            the image

    Returns:
        image|None: Returns the generated Image object upon successful
            build. Otherwise, value will be None
        build_results: The formatted log of the build steps
        Build.STATUS: The build status. Either `IN_PROGRESS` or `ERROR`
    """
    try:
        image, build_result = _docker_build_image(
            docker_client, full_image_name, workdir
        )
        build_results = _format_build_results(build_result)
        return image, build_results, Build.IN_PROGRESS
    except (APIError, BuildError) as exc:
        build_results = (
            _format_build_results(exc.build_log)
            if hasattr(exc, "build_log")
            else str(exc)
        )
        return None, build_results, Build.ERROR


def _docker_build_image(
    docker_client: DockerClient, full_image_name: str, workdir: str
) -> tuple[Union[Image, None], str]:
    return docker_client.images.build(
        path=workdir, pull=True, forcerm=True, tag=full_image_name
    )


def _push_image(docker_client: DockerClient, full_image_name: str) -> tuple[str, str]:
    """Push given image name

    Args:
        docker_client: The DockerClient to interface with the Docker socket.
        full_image_name: The string of the full image name, which includes the
            registry to push to and image tag.

    Returns:
        push_results: The formatted string of the push results
        Build.STATUS: The status of the build step. Either `COMPLETE`
            or `ERROR`
    """
    try:
        push_result = docker_client.images.push(full_image_name, stream=True)
        return _format_push_results(push_result), Build.COMPLETE
    except APIError as exc:
        logger.error(f"Failed to push image: {full_image_name}. Error: {exc}")
        return None, Build.ERROR


def _update_build_status(build: Build):
    """Update the status of the build in the database"""
    match build.status:
        case Build.COMPLETE:
            build.complete()
        case Build.ERROR:
            build.error()
        case Build.IN_PROGRESS:
            build.in_progress()
        case Build.PENDING:
            build.pending()
        case _:
            logger.error(f"Unknown build status for {build}: {build.status}")
            build.error()


def _save_functions(
    functions: list[Function], function_parameters: list[FunctionParameter]
):
    """Save all functions and associated function parameters"""
    # TODO: Try to optimize the saving of these objects to improve performance
    for func in functions:
        func.save()

    for parameter in function_parameters:
        parameter.save()


def _delete_removed_functions(
    function_definitions: list[dict],
    function_parameters: list[FunctionParameter],
    package: Package,
) -> None:
    """Delete any functions that have been removed from the package definition"""
    _delete_removed_function_parameters(function_parameters, package)
    _deactivate_removed_functions(function_definitions, package)


def _cleanup(
    docker_client: DockerClient, image: Image, workdir: str, build_id: UUID
) -> None:
    """Cleanup artifacts generated from the build process"""
    logger.debug(f"Cleaning up remnants of build {build_id}")

    shutil.rmtree(workdir)
    try:
        docker_client.images.remove(image.id, force=True)
    except DockerException:
        logger.warn(f"Unable to remove build image: {image.id}")


def _get_docker_client() -> DockerClient:
    """Creates a new docker client

    Args:
        None

    Returns:
        docker_client: A new docker client

    Raises:
        DockerSocketConnectionError: Raised when a connection to the Docker socket
        could not be created.
    """
    try:
        return docker.from_env()
    except DockerException as err:
        logger.fatal("Failed to connect to the Docker socket. Unable to build.")
        raise DockerSocketConnectionError(err)


def _update_log(log: str, log_msg: str) -> str:
    """Return the new log with the log join'd with the log message

    Args:
        log: The original log string
        log_msg: The string to concatenate to the log

    Returns:
        log: The new log message
    """
    if log == "":
        return log_msg

    return "\n".join([log, log_msg])
