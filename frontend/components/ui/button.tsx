import { ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md" | "icon";
};

export function Button({ className, variant = "primary", size = "md", ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-md border font-medium transition disabled:cursor-not-allowed disabled:opacity-50",
        size === "sm" && "h-8 px-3 text-xs",
        size === "md" && "h-10 px-4 text-sm",
        size === "icon" && "h-9 w-9 p-0",
        variant === "primary" && "border-ink bg-ink text-paper hover:bg-[#26302e]",
        variant === "secondary" && "border-line bg-panel text-ink hover:bg-[#f0eadc]",
        variant === "ghost" && "border-transparent bg-transparent text-ink hover:bg-[#eee8da]",
        variant === "danger" && "border-risk bg-risk text-white hover:bg-[#9d332b]",
        className
      )}
      {...props}
    />
  );
}

