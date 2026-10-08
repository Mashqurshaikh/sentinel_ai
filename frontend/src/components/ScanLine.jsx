import { motion } from 'framer-motion'

// The signature moment of the Gateway page: while a prompt is being
// analyzed, a bright line sweeps down the input like a document scanner
// or checkpoint X-ray, before results resolve. Purely visual - the real
// work happens on the backend - but it dramatizes what "scanning" means.
export default function ScanLine({ active }) {
  if (!active) return null
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden rounded-xl">
      <motion.div
        initial={{ top: '-10%', opacity: 0 }}
        animate={{ top: '105%', opacity: [0, 1, 1, 0] }}
        transition={{ duration: 1.3, ease: [0.4, 0, 0.2, 1] }}
        className="absolute left-0 right-0 h-24"
        style={{
          background: 'linear-gradient(180deg, transparent 0%, rgba(255,176,32,0.18) 40%, rgba(255,176,32,0.85) 50%, rgba(255,176,32,0.18) 60%, transparent 100%)',
        }}
      />
      <motion.div
        initial={{ top: '-2%', opacity: 0 }}
        animate={{ top: '105%', opacity: [0, 1, 1, 0] }}
        transition={{ duration: 1.3, ease: [0.4, 0, 0.2, 1] }}
        className="absolute left-0 right-0 h-[2px] bg-brand shadow-[0_0_12px_2px_rgba(255,176,32,0.8)]"
      />
    </div>
  )
}
