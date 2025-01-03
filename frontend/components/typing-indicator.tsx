export function TypingIndicator() {
  return (
    <div className="flex space-x-1 items-center justify-center h-5 sm:h-6">
      {[0, 1, 2].map((index) => (
        <div
          key={index}
          className={"h-2 w-2 rounded-full bg-foreground animate-bounce-slight"}
          style={{ animationDelay: `${index * 0.2}s`}}
        />
      ))}
    </div>
  )
}