chrome.runtime.sendMessage({
    type: 'saveHistory',
    url: window.location.href
});

