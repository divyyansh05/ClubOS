export function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 py-1" aria-label="Loading response">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="w-1.5 h-1.5 rounded-full bg-info-light dark:bg-info-dark opacity-60 animate-bounce"
          style={{ animationDelay: `${i * 150}ms` }}
        />
      ))}
    </div>
  );
}
