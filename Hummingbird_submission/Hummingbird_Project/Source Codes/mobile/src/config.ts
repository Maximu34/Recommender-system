/**
 * Backend address.
 *
 * The app runs on a phone and the backend runs on your laptop, so this can
 * never be "localhost" — that would point at the phone itself. Use the LAN
 * address that `scripts/install_gate.py` prints, and make sure the phone and
 * the laptop are on the same Wi-Fi network.
 *
 * Start the backend with `--host 0.0.0.0` or it will refuse connections from
 * the phone even when the address is right.
 */
export const API_BASE = 'http://192.168.110.243:8000';

/** How many recommendations to request. */
export const RESULT_COUNT = 20;

/** Maximum hum length, in milliseconds. */
export const MAX_HUM_MS = 10000;
