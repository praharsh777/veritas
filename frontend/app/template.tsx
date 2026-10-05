// Re-mounts on every navigation, giving each page a soft entrance animation.
export default function Template({ children }: { children: React.ReactNode }) {
  return <div className="animate-fadeUp">{children}</div>;
}
