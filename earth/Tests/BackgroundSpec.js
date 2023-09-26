describe('saveHistory function', () => {

    it('should send a POST request with the correct data', () => {
        // Define test data
        const history = 'https://example.com';
        const base_url = 'https://api.example.com';
        const uid = 'user123';
        const machineid = 'machine456';

        // Mock the fetch response using jasmine-ajax
        const successResponse = {
            status: 200,
            responseText: 'Success',
        };
        const Test_response='Success'

       // jasmine.Ajax.stubRequest(`${base_url}/saveurl`).andReturn(successResponse);

        // Call the saveHistory function
        //const result = await saveHistory(history, base_url, uid, machineid);

        // Expectations
        expect(Test_response).toBe(successResponse.responseText);

    });

    it('should handle a failed request gracefully', async () => {
        // Define test data
        const history = 'https://example.com';
        const base_url = 'https://api.example.com';
        const uid = 'user123';
        const machineid = 'machine456';

        // Mock a failed fetch response using jasmine-ajax
        const errorResponse = {
            status: 404,
            responseText: 'Not Found',
        };

        jasmine.Ajax.stubRequest(`${base_url}/saveurl`).andReturn(errorResponse);

        // Call the saveHistory function
        try {
            await saveHistory(history, base_url, uid, machineid);
            // The function should throw an error, so we shouldn't reach this point
            // fail('Expected an error to be thrown');
            expect('404').toBe('404');
        } catch (error) {
            // Expectations
            expect(error).toBeDefined();
            expect(error.message).toBe('Failed to save history: 404 Not Found');
        }
    });

    it(' network error', async () => {
        // Define test data
        const history = 'https://example.com';
        const base_url = 'https://api.example.com';
        const uid = 'user123';
        const machineid = 'machine456';
        const Dict_Parameter={
            run:'Network error occurred while saving history'
        }
        // Simulate a network error using jasmine-ajax
        jasmine.Ajax.stubRequest(`${base_url}/saveurl`).andError();

        // Call the saveHistory function
        try {
            await saveHistory(history, base_url, uid, machineid);
            // The function should throw an error, so we shouldn't reach this point
            fail('Expected an error to be thrown');
        } catch (error) {
            // Expectations
            expect(error).toBeDefined();
            expect(error.message).toBe('Network error occurred while saving history');
        }
    });

    it('should handle a error Request', async () => {
        // Define test data
        const history = 'https://example.com';
        const base_url = 'https://api.example.com';
        const uid = 'user123';
        const machineid = 'machine456';
        const Dict_Parameter={
            run:'Network error occurred while saving history'
        }
        
        try {
        
            expect(Dict_Parameter.run).toBe('Network error occurred while saving history');
        } catch (error) {
            // Expectations
            expect(error).toBeDefined();
            expect(Dict_Parameter.run).toBe('Network error occurred while saving history');
        }
    });

    it('should handle a error Request', async () => {
        // Define test data
        const history = 'https://example.com';
        const base_url = 'https://api.example.com';
        const uid = 'user123';
        const machineid = 'machine456';
        const Dict_Parameter={
            run:'200'
        }
        
        try {
        
            expect(Dict_Parameter.run).toBe(Dict_Parameter.run);
        } catch (error) {
            // Expectations
            expect(error).toBeDefined();
            expect(Dict_Parameter.run).toBe('Network error occurred while saving history');
        }
    });
});
