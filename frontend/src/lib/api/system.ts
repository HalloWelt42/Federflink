/** System-API: Health und Capabilities. */

import { requestJson } from './http'
import type { CapabilitiesAntwort, HealthAntwort } from './typen'

export function ladeHealth(): Promise<HealthAntwort> {
  return requestJson<HealthAntwort>('/api/health')
}

export function ladeCapabilities(): Promise<CapabilitiesAntwort> {
  return requestJson<CapabilitiesAntwort>('/api/capabilities')
}
