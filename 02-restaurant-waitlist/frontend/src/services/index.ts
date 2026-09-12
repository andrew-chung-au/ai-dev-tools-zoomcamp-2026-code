import { MockWaitlistService } from "./mockWaitlistService";
import type { WaitlistService } from "./waitlistService";

/**
 * The single active service instance used by the whole app.
 * Swap this for a FastAPI-backed client in the backend phase.
 */
export const waitlistService: WaitlistService = new MockWaitlistService();

export * from "./waitlistService";
export { MockServiceError, MockWaitlistService } from "./mockWaitlistService";
