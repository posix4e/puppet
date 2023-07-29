// popup.js
document.getElementById('config-form').addEventListener('submit', function(e) {
    e.preventDefault(); // Prevent the form from being submitted

    const base_url = document.getElementById('base_url').value;
    const uid = document.getElementById('uid').value;
    const machineid = document.getElementById('machineid').value;

    // Save the values to chrome.storage
    chrome.storage.sync.set({
        base_url: base_url,
        uid: uid,
        machineid: machineid
    }, function() {
        console.log('Settings saved');
    });
});
