import { ApiWaitlistService } from "./apiWaitlistService";
import { MockWaitlistService } from "./mockWaitlistService";
import type { WaitlistService } from "./waitlistService";

/**
 * Set VITE_USE_MOCK_SERVICE=true to force the in-memory mock (e.g. for
 * offline frontend work). Vitest runs with MODE="test", so unit tests get
 * the mock automatically. Everything else (dev, build) talks to the real
 * FastAPI backend — see apiWaitlistService.ts for VITE_API_BASE_URL.
 */
const useMock =
  import.meta.env.MODE === "test" || import.meta.env.VITE_USE_MOCK_SERVICE === "true";

/**
 * The single active service instance used by the whole app.
 */
export const waitlistService: WaitlistService = useMock
  ? new MockWaitlistService()
  : new ApiWaitlistService();

export * from "./waitlistService";
export { ApiServiceError, ApiWaitlistService } from "./apiWaitlistService";
export { MockServiceError, MockWaitlistService } from "./mockWaitlistService";
