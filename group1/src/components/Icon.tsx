interface IconProps {
  name: string;
  size?: number;
  filled?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

export function Icon({ name, size = 24, filled = false, className = '', style }: IconProps) {
  return (
    <span
      className={`material-symbols-outlined ${filled ? 'filled' : ''} ${className}`}
      style={{ fontSize: `${size}px`, ...style }}
      aria-hidden="true"
    >
      {name}
    </span>
  );
}
