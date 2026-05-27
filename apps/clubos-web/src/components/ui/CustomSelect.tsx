import { useState, useRef, useEffect } from 'react'

interface SelectOption {
  value: string
  label: string
  group?: string
}

interface CustomSelectProps {
  options: SelectOption[]
  value: string
  onChange: (value: string) => void
  placeholder?: string
  className?: string
}

export function CustomSelect({
  options,
  value,
  onChange,
  placeholder = 'Select metric',
  className = '',
}: CustomSelectProps) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  // Close on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  // Close on Escape
  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (e.key === 'Escape') setOpen(false)
    }
    document.addEventListener('keydown', handleKey)
    return () => document.removeEventListener('keydown', handleKey)
  }, [])

  const selected = options.find(o => o.value === value)

  // Group options if group field is present
  const groups = options.reduce((acc, opt) => {
    const g = opt.group || ''
    if (!acc[g]) acc[g] = []
    acc[g].push(opt)
    return acc
  }, {} as Record<string, SelectOption[]>)

  const hasGroups = Object.keys(groups).some(g => g !== '')

  return (
    <div ref={ref} className={`relative ${className}`}>
      {/* Trigger button — matches ClubOS card style */}
      <button
        onClick={() => setOpen(prev => !prev)}
        className={`
          w-full flex items-center justify-between
          px-3 py-2
          bg-[var(--color-bg-secondary,#F5F0E8)]
          dark:bg-[var(--color-bg-secondary-dark,#2A2520)]
          border border-[var(--color-border,#C8BFA8)]
          dark:border-[var(--color-border-dark,#4A4035)]
          rounded-sm
          font-mono text-xs uppercase tracking-wider
          text-[var(--color-ink,#2C2620)]
          dark:text-[var(--color-ink-dark,#E8E0D0)]
          hover:border-[var(--color-accent,#8B5E3C)]
          transition-colors duration-150
          cursor-pointer
          text-left
        `}
        aria-expanded={open}
        aria-haspopup="listbox"
      >
        <span className="truncate">
          {selected ? selected.label : placeholder}
        </span>
        <span
          className={`ml-2 flex-shrink-0 transition-transform duration-150
            ${open ? 'rotate-180' : ''}`}
          aria-hidden
        >
          ▾
        </span>
      </button>

      {/* Dropdown panel */}
      {open && (
        <div
          className={`
            absolute z-50 mt-1 w-full min-w-[200px]
            bg-[var(--color-card,#FAF7F2)]
            dark:bg-[var(--color-card-dark,#1E1A16)]
            border border-[var(--color-border,#C8BFA8)]
            dark:border-[var(--color-border-dark,#4A4035)]
            rounded-sm shadow-lg
            max-h-64 overflow-y-auto
          `}
          role="listbox"
        >
          {hasGroups
            ? Object.entries(groups).map(([group, opts]) => (
                <div key={group}>
                  {group && (
                    <div className="
                      px-3 py-1.5
                      font-mono text-[10px] uppercase tracking-widest
                      text-[var(--color-ink3,#8C7D6A)]
                      dark:text-[var(--color-ink3-dark,#6A5D50)]
                      border-b border-[var(--color-border,#C8BFA8)]
                      dark:border-[var(--color-border-dark,#4A4035)]
                      bg-[var(--color-bg-secondary,#F5F0E8)]
                      dark:bg-[var(--color-bg-secondary-dark,#2A2520)]
                    ">
                      {group}
                    </div>
                  )}
                  {opts.map(opt => (
                    <button
                      key={opt.value}
                      onClick={() => { onChange(opt.value); setOpen(false) }}
                      className={`
                        w-full text-left px-3 py-2
                        font-mono text-xs
                        transition-colors duration-100
                        ${opt.value === value
                          ? 'bg-[var(--color-accent-bg,#F0E8E0)] dark:bg-[var(--color-accent-bg-dark,#3A2E24)] text-[var(--color-accent,#8B5E3C)]'
                          : 'text-[var(--color-ink2,#5C4F40)] dark:text-[var(--color-ink2-dark,#C0B0A0)] hover:bg-[var(--color-bg-hover,#EDE8DC)] dark:hover:bg-[var(--color-bg-hover-dark,#2E2820)]'
                        }
                      `}
                      role="option"
                      aria-selected={opt.value === value}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              ))
            : options.map(opt => (
                <button
                  key={opt.value}
                  onClick={() => { onChange(opt.value); setOpen(false) }}
                  className={`
                    w-full text-left px-3 py-2
                    font-mono text-xs
                    transition-colors duration-100
                    ${opt.value === value
                      ? 'bg-[var(--color-accent-bg,#F0E8E0)] text-[var(--color-accent,#8B5E3C)]'
                      : 'text-[var(--color-ink2,#5C4F40)] hover:bg-[var(--color-bg-hover,#EDE8DC)]'
                    }
                  `}
                  role="option"
                  aria-selected={opt.value === value}
                >
                  {opt.label}
                </button>
              ))
          }
        </div>
      )}
    </div>
  )
}
