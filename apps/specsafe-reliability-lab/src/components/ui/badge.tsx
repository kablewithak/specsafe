import { cva, type VariantProps } from "class-variance-authority";
import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold tracking-wide",
  {
    variants: {
      variant: {
        neutral: "border-white/10 bg-white/5 text-white/70",
        success: "border-emerald-400/25 bg-emerald-400/10 text-emerald-200",
        danger: "border-rose-400/30 bg-rose-400/10 text-rose-200",
        accent: "border-amber-300/25 bg-amber-300/10 text-amber-100",
      },
    },
    defaultVariants: { variant: "neutral" },
  },
);

type BadgeProps = HTMLAttributes<HTMLSpanElement> & VariantProps<typeof badgeVariants>;

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}
