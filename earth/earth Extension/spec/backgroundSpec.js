
describe("Chrome Extension Background Script", function () {
  beforeEach(function () {
    spyOn(chrome.runtime, 'onMessage').and.callFake((listener) => {
      listener({ type: 'saveHistory', url: 'https://testurl.com' }, {}, jasmine.createSpy('sendResponse'));
    });

    spyOn(chrome.storage.sync, 'get').and.callFake((keys, callback) => {
      const result = {
        base_url: 'https://apitest.com',
        uid: 'user123',
        machineid: 'machine123',
      };
      callback(result);
    });

    spyOn(window, 'fetch').and.returnValue(Promise.resolve({ text: () => Promise.resolve('Success') }));
  });

  it("should handle 'saveHistory' message", async function () {
    await chrome.runtime.onMessage.calls.mostRecent().args[0](
      { type: 'saveHistory', url: 'https://apitest.com' },
      {},
      jasmine.createSpy('sendResponse')
    );

    // Expectations for the function call and fetch request
    expect(chrome.storage.sync.get).toHaveBeenCalledWith(['base_url', 'uid', 'machineid'], jasmine.any(Function));
    expect(window.fetch).toHaveBeenCalledWith('https://apitest.com/saveurl', jasmine.any(Object));
  });

  it("should not handle other message types", async function () {
    await chrome.runtime.onMessage.calls.mostRecent().args[0]({ type: 'otherType' }, {}, jasmine.createSpy('sendResponse'));
    expect(chrome.storage.sync.get).not.toHaveBeenCalled();
    expect(window.fetch).not.toHaveBeenCalled();
  });

  it("should handle 'anotherMessageType' message", async function () {

    await chrome.runtime.onMessage.calls.mostRecent().args[0]({ type: 'anotherMessageType' }, {}, jasmine.createSpy('sendResponse'));

  });

  it("should handle 'nullMessage' message", async function () {

    await chrome.runtime.onMessage.calls.mostRecent().args[0]({ type: null }, {}, jasmine.createSpy('sendResponse'));

  });


});
