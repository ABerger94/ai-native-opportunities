const entityMap: Record<string, string> = {
  amp: "&",
  lt: "<",
  gt: ">",
  quot: '"',
  apos: "'",
  nbsp: " "
};

export function decodeHtml(value: string): string {
  return value
    .replace(/&#(\d+);/g, (_, code: string) => String.fromCharCode(Number(code)))
    .replace(/&([a-z]+);/gi, (_, entity: string) => entityMap[entity.toLowerCase()] ?? `&${entity};`);
}

export function htmlToText(value: string): string {
  return decodeHtml(
    value
      .replace(/<script[\s\S]*?<\/script>/gi, " ")
      .replace(/<style[\s\S]*?<\/style>/gi, " ")
      .replace(/<\/(p|div|h[1-6]|li|ul|ol)>/gi, "\n")
      .replace(/<br\s*\/?>/gi, "\n")
      .replace(/<[^>]+>/g, " ")
  )
    .replace(/[ \t]+/g, " ")
    .replace(/\n\s+/g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

export function formatDate(value: string | null): string {
  if (!value) {
    return "Not listed";
  }
  return new Intl.DateTimeFormat("en", { dateStyle: "medium" }).format(new Date(value));
}
