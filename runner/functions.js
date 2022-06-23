function hello() {
    console.log("Hello Docker World")
}


function hello_name({ who = "Docker", }) {
    console.log(`Hello ${who}`)
    return `Hello ${who}!`
}

export { hello, hello_name }