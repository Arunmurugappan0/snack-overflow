import { describe, expect, it } from 'vitest';

import { errorMessage } from './api.js';

describe('API error messages', () => {
  it('shows the server message for a stock conflict', () => {
    expect(errorMessage({
      response: {
        status: 409,
        data: { error: { code: 'INSUFFICIENT_STOCK', message: 'Someone beat you to the last packet!' } },
      },
    })).toBe('Someone beat you to the last packet!');
  });

  it('explains a connection failure without masking it as success', () => {
    expect(errorMessage({ request: {} })).toBe(
      'Could not reach the pantry API. Check your connection and try again.',
    );
  });
});
