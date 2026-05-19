export const FIRST_RELEASE = new Date('2008-08-04T00:00:00Z');

export function yearsSinceFirstRelease(now: Date = new Date()): number {
  const ms = now.getTime() - FIRST_RELEASE.getTime();
  return Math.floor(ms / (365.25 * 24 * 60 * 60 * 1000));
}
