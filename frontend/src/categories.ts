export type Category = "normal" | "printed" | "liquid";

export const CATEGORY_LABEL: Record<Category, string> = {
  normal: "普通",
  printed: "印刷",
  liquid: "液体",
};

export const CATEGORY_OPTIONS: Category[] = ["normal", "printed", "liquid"];

export function categoryClass(category: string): string {
  return `cat-badge cat-${category}`;
}
