import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { ShieldCheck, Lock, User, Building2, Loader2, AlertCircle } from 'lucide-react'
import { useAuth } from '../auth/AuthContext'

export default function Login() {
  const { login, register } = useAuth()
  const navigate = useNavigate()
  const [mode, setMode] = useState('login') // 'login' | 'register'
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [department, setDepartment] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      if (mode === 'login') {
        await login(username, password)
      } else {
        await register({ username, password, full_name: fullName, department: department || 'Unassigned' })
      }
      navigate('/')
    } catch (err) {
      setError(err?.response?.data?.detail || 'Something went wrong. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-bg px-4 relative overflow-hidden">
      {/* soft ambient glow behind the card - the same amber accent used
          throughout, just dialed down for a light backdrop */}
      <div className="absolute w-[32rem] h-[32rem] rounded-full bg-brand/10 blur-3xl animate-glow" style={{ top: '-8rem', left: '-6rem' }} />
      <div className="absolute w-[28rem] h-[28rem] rounded-full bg-info/10 blur-3xl animate-glow" style={{ bottom: '-6rem', right: '-4rem' }} />

      <motion.div
        initial={{ opacity: 0, y: 16, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.45, ease: [0.4, 0, 0.2, 1] }}
        className="relative w-full max-w-md rounded-2xl border border-line bg-surface shadow-xl shadow-black/5 p-8"
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1, type: 'spring', stiffness: 200, damping: 14 }}
          className="w-14 h-14 rounded-2xl bg-brand/10 flex items-center justify-center mb-5"
        >
          <ShieldCheck size={28} className="text-brand" />
        </motion.div>

        <h1 className="font-display text-2xl font-semibold text-ink mb-1">
          {mode === 'login' ? 'Welcome back' : 'Create an account'}
        </h1>
        <p className="text-sm text-muted mb-6">
          {mode === 'login' ? 'Sign in to Sentinel to scan a prompt or review the queue.' : 'Employee accounts can use the Gateway right away.'}
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <AnimatePresence>
            {mode === 'register' && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="flex flex-col gap-4 overflow-hidden"
              >
                <div>
                  <label className="text-xs text-muted font-mono block mb-1">full name</label>
                  <div className="relative">
                    <User size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
                    <input
                      value={fullName}
                      onChange={e => setFullName(e.target.value)}
                      placeholder="Enter your full name"
                      className="w-full rounded-lg bg-surface-2 border border-line pl-9 pr-3 py-2.5 text-sm focus:outline-none focus:border-brand placeholder:text-muted/60"
                    />
                  </div>
                </div>
                <div>
                  <label className="text-xs text-muted font-mono block mb-1">department</label>
                  <div className="relative">
                    <Building2 size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
                    <input
                      value={department}
                      onChange={e => setDepartment(e.target.value)}
                      placeholder="Enter department"
                      className="w-full rounded-lg bg-surface-2 border border-line pl-9 pr-3 py-2.5 text-sm focus:outline-none focus:border-brand placeholder:text-muted/60"
                    />
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <div>
            <label className="text-xs text-muted font-mono block mb-1">username</label>
            <div className="relative">
              <User size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
              <input
                value={username}
                onChange={e => setUsername(e.target.value)}
                placeholder="Enter username"
                required
                className="w-full rounded-lg bg-surface-2 border border-line pl-9 pr-3 py-2.5 text-sm focus:outline-none focus:border-brand placeholder:text-muted/60"
              />
            </div>
          </div>

          <div>
            <label className="text-xs text-muted font-mono block mb-1">password</label>
            <div className="relative">
              <Lock size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="Enter password"
                required
                className="w-full rounded-lg bg-surface-2 border border-line pl-9 pr-3 py-2.5 text-sm focus:outline-none focus:border-brand placeholder:text-muted/60"
              />
            </div>
          </div>

          <AnimatePresence>
            {error && (
              <motion.p
                initial={{ opacity: 0, y: -6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="text-sm text-danger flex items-center gap-1.5"
              >
                <AlertCircle size={14} /> {error}
              </motion.p>
            )}
          </AnimatePresence>

          <motion.button
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.98 }}
            type="submit"
            disabled={busy}
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-brand text-onbrand font-semibold px-4 py-2.5 text-sm hover:brightness-110 transition disabled:opacity-50"
          >
            {busy && <Loader2 size={15} className="animate-spin" />}
            {mode === 'login' ? 'Sign in' : 'Create account'}
          </motion.button>
        </form>

        <p className="text-sm text-muted text-center mt-6">
          {mode === 'login' ? (
            <>New here? <button onClick={() => { setMode('register'); setError('') }} className="text-brand font-medium hover:underline">Create an employee account</button></>
          ) : (
            <>Already have an account? <button onClick={() => { setMode('login'); setError('') }} className="text-brand font-medium hover:underline">Sign in</button></>
          )}
        </p>

        {mode === 'login' && (
          <p className="text-xs text-muted text-center mt-3 font-mono">
            demo admin: admin / admin123
          </p>
        )}
      </motion.div>
    </div>
  )
}
