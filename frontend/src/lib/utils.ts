/**
 * Shared utility functions for the frontend.
 *
 * Provides the `cn` helper for merging Tailwind CSS class names,
 * resolving conflicts between clsx and tailwind-merge.
 */
import type { ClassValue } from "clsx"
import { clsx } from "clsx"
import { twMerge } from "tailwind-merge"

/**
 * Merge CSS class names, resolving Tailwind CSS conflicts.
 *
 * Combines clsx (for conditional class merging) with tailwind-merge
 * (for deduplicating conflicting Tailwind utilities).
 *
 * @param inputs - Any number of class values (strings, arrays, objects).
 * @returns A merged, deduplicated class string.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
