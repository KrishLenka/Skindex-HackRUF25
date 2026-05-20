import clsx from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Utility function to conditionally merge Tailwind CSS classes safely resolving conflicts.
 * @param {...*} inputs - Conditional class literals or structures to parse.
 * @returns {string} A normalized string of tailwind classes.
 */
export function cn(...inputs) {
  return twMerge(clsx(...inputs));
}
