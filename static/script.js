window.onload = function(){
    var pass = document.getElementById("password");
    pass.addEventListener("input", checkAllConditions);
}

// Checks for all necessary password conditions
function checkAllConditions(){
    checkLength()
    checkCapital()
    checkLowercase()
    checkNumber()
}

function checkLength(){
    var pwd = document.getElementById("password").value;
    if (pwd.length >= 8)
    {
        document.getElementById("lengthimg").src = "../static/checkbox icon.png";
        document.getElementById("length").style.color = "green"
    }
    else
    {
        document.getElementById("lengthimg").src = "../static/redx2.png";
        document.getElementById("length").style.color = "red"
    }
}

function checkLowercase(){
    var pwd = document.getElementById("password").value;
    if (pwd.toUpperCase() != pwd)
    {
        document.getElementById("lowercaseimg").src = "../static/checkbox icon.png";
        document.getElementById("lowercase").style.color = "green"
    }
    else
    {
        document.getElementById("lowercaseimg").src = "../static/redx2.png";
        document.getElementById("lowercase").style.color = "red"
    }
}

function checkCapital(){
    var pwd = document.getElementById("password").value;
    if (pwd.toLowerCase() != pwd)
    {
        document.getElementById("capitalimg").src = "../static/checkbox icon.png";
        document.getElementById("capital").style.color = "green"
    }
    else
    {
        document.getElementById("capitalimg").src = "../static/redx2.png";
        document.getElementById("capital").style.color = "red"
    }
}

function checkNumber(){
    var pwd = document.getElementById("password").value;
    console.log("checking the number");
    if (/\d+/.test(pwd))
    {
        document.getElementById("numberimg").src = "../static/checkbox icon.png";
        document.getElementById("number").style.color = "green"
    }
    else
    {
        document.getElementById("numberimg").src = "../static/redx2.png";
        document.getElementById("number").style.color = "red"
    }
}
