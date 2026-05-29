const cookies = await chrome.cookies.getAll({"url": 'https://x.com'});

const cookiesDict = {};

cookies.forEach(c => {
    cookiesDict[c.name] = c.value;
})
const json = JSON.stringify(cookiesDict);
document.querySelector('textarea').innerText = json;