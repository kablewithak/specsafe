type SectionHeadingProps = {
  eyebrow: string;
  title: string;
  description: string;
};

export function SectionHeading({ eyebrow, title, description }: SectionHeadingProps) {
  return (
    <div className="max-w-3xl space-y-3">
      <p className="font-mono text-xs uppercase tracking-[0.22em] text-amber-200/80">{eyebrow}</p>
      <h2 className="text-balance text-3xl font-semibold tracking-tight text-white md:text-4xl">
        {title}
      </h2>
      <p className="text-pretty text-base leading-7 text-white/58 md:text-lg">{description}</p>
    </div>
  );
}
