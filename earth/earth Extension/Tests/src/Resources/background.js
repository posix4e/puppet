chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.type === 'saveHistory') {
        chrome.storage.sync.get(['base_url', 'uid', 'machineid'], function(result) {
            saveHistory(request.url, result.base_url, result.uid, result.machineid)
                .then(() => console.log('History Saved Successfully'))
                .catch(error => console.log('error', error));
        });
    }
});

async function saveHistory(history, base_url, uid, machineid) {
    console.log(history)
    console.log(machineid)
    console.log(uid)
    console.log(`${base_url}/saveurl`)
    var requestOptions = {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json', // Set the content type to JSON
        },
  
        body: JSON.stringify({
            url: history,
            machineid: machineid,
            uid: uid
        }),
        redirect: 'follow'
    };
    const response = await fetch(`${base_url}/saveurl`, requestOptions);
    return await response.text();
}
