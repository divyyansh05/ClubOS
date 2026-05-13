/**
 * Format date string to "Month YY" format (e.g., "January 26")
 * @param dateString - Date string in format YYYY-MM-DD or ISO format
 * @returns Formatted date string like "January 26"
 */
export function formatMonthYear(dateString: string): string {
  if (!dateString) return "";

  const date = new Date(dateString);
  const month = date.toLocaleDateString("en-US", { month: "long" });
  const year = date.toLocaleDateString("en-US", { year: "2-digit" });

  return `${month} ${year}`;
}

/**
 * Format date string to "Mon YY" format for compact display (e.g., "Jan 26")
 * @param dateString - Date string in format YYYY-MM-DD or ISO format
 * @returns Formatted date string like "Jan 26"
 */
export function formatMonthYearShort(dateString: string): string {
  if (!dateString) return "";

  const date = new Date(dateString);
  const month = date.toLocaleDateString("en-US", { month: "short" });
  const year = date.toLocaleDateString("en-US", { year: "2-digit" });

  return `${month} ${year}`;
}
