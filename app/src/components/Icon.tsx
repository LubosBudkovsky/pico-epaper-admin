export default function Icon({name, size}: {name: string, size?: number}) {
  return <i className={`icon bi-${name}`} style={{ fontSize: size ? `${size}px` : undefined }}></i>;
}