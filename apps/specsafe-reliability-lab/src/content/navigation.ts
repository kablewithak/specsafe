export type PrimaryNavigationItem = Readonly<{
  number: string;
  label: string;
  href: `#${string}`;
}>;

export const primaryNavigation = [
  {
    number: "01",
    label: "Problem",
    href: "#why-it-matters",
  },
  {
    number: "02",
    label: "Question",
    href: "#north-star",
  },
  {
    number: "03",
    label: "Results",
    href: "#policy-results",
  },
  {
    number: "04",
    label: "Safety gate",
    href: "#confidence-gate",
  },
  {
    number: "05",
    label: "Meaning",
    href: "#what-it-means",
  },
  {
    number: "06",
    label: "Evidence",
    href: "#evidence",
  },
] as const satisfies readonly PrimaryNavigationItem[];
