import { useMemo, useRef, useState, useEffect } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const exampleTextByLang = {
  fa: 'جانوَران یا حیوانات، جاندارانی یوکاریوت و چندیاخته‌ای (چندسلولی) هستند، که در مجموع تشکیل‌دهندهٔ فرمانروی زیست‌شناسی جانوران هستند و شامل دو شاخه اصلی مهره‌داران و بی‌مهرگان هستند. جانوران به‌جز چند استثنا، دارای تنفس سلولی، قابلیت حرکت و تولیدمثل جنسی هستند. جانوران برخلاف گیاهان و جلبک‌ها قادر به تولید مواد آلیمورد نیاز خود نیستند و زندگی دگرپروردگی دارند. تا کنون بیش از ۱٫۵ میلیون گونه از جانوران، شناسایی و توصیف شده‌اند که حدود یک میلیون از آن‌ها، حشره هستند. بسیاری از گونه‌های جانوری، تاکنون شناسایی نشده‌اند اما برآورد می‌شود که جانوران شامل بیش از ۷ میلیون گونه هستند.\n\nدر تعریف زیست‌شناسی به سلسله جانوران (Animalia)، پُریاختگان هم گفته می‌شود که بدین گونه تعریف می‌شود: سلسله‌ای از ارگانیسم‌های پُریاخته که از رویان تکوین می‌یابند.\n\nباور بر این است که جانوران، طی فرگشت از یوکاریوت‌های تک‌سلولی ایجاد شده‌اند که اولین بار توانستند در کنار هم رشد کنند. ابتدا همزیستی بین دو پروکاریوت که یکی دیگری را «که منشأ یوکاریوت‌هاست» بالاتر برد و نسل آن ادامه یافت. پس از به وجود آمدن سلول‌های دارای میتوکندری نقطهٔ عطف دیگر، توانایی انتقال پیام بین سلول‌ها بود. گروهی در ارتباط با محیط بیرون ماندند و فضای درونشان به محیط داخلی فرگشت پیدا کرد، گروهی دیگر نیز به تولیدمثل اختصاص یافتند. بعدها ارتباط‌های سلولی شامل پروتئین‌ها شد. همهٔ جانوران دگرپَرورد (heterotroph) هستند یعنی برای تأمین انرژی و رفع نیازهای غذایی خود از مواد آلی ساخته‌شدهٔ دیگر جانداران استفاده می‌کنند. تمامی جانوران به جز اسفنج‌ها هوپس زیان هستند و جانوران به این گونه تقسیم می‌شود:\n\nمهره‌داران: پستانداران، پرندگان، خزندگان، دوزیستان و ماهیان\n\nبی‌مهرگان: نرم‌تنان، دوکفه‌ها، هشت‌پایان، کیسه‌تنان (مرجان‌ها)، خارپوستان، بندپایان، کرم‌ها و اسفنج‌ها',
  en: 'In recent decades, digital transformation has reshaped social and economic structures. Technologies like the internet, AI, and big data have changed how people communicate and make decisions.',
}



const levelToPercentage = {
  'very-short': 20,
  short: 35,
  medium: 50,
  long: 70,
}

const methods = [
  {
    id: 'extractive',
    title: 'استخراجی',
    tag: 'Extractive',
    subtitle: 'TextRank برای حفظ کلمات کلیدی',
  },
  {
    id: 'abstractive',
    title: 'مولد',
    tag: 'Abstractive',
    subtitle: 'مدل ترنسفورمر فارسی',
  },
  {
    id: 'hybrid',
    title: 'ترکیبی',
    tag: 'Hybrid',
    subtitle: 'استخراجی سپس مولد',
  },
]
const DEFAULT_ABSTRACTIVE_SETTINGS = {
  numBeams: 2,
  lengthPenalty: 1.0,
  repetitionPenalty: 1.1,
  noRepeatNgramSize: 3,
}

function App() {
  const [text, setText] = useState('')
  const [method, setMethod] = useState('extractive')
  const [summaryLevel, setSummaryLevel] = useState('medium')
  const [hybridExtractiveRatio, setHybridExtractiveRatio] = useState(50)
  const [abstractiveNumBeams, setAbstractiveNumBeams] = useState(
    DEFAULT_ABSTRACTIVE_SETTINGS.numBeams,
  )
  const [abstractiveLengthPenalty, setAbstractiveLengthPenalty] = useState(
    DEFAULT_ABSTRACTIVE_SETTINGS.lengthPenalty,
  )
  const [abstractiveRepetitionPenalty, setAbstractiveRepetitionPenalty] = useState(
    DEFAULT_ABSTRACTIVE_SETTINGS.repetitionPenalty,
  )
  const [abstractiveNoRepeatNgramSize, setAbstractiveNoRepeatNgramSize] = useState(
    DEFAULT_ABSTRACTIVE_SETTINGS.noRepeatNgramSize,
  )
  const [abstractiveAdvancedEnabled, setAbstractiveAdvancedEnabled] = useState(false)
  const [abstractiveAdvancedOpen, setAbstractiveAdvancedOpen] = useState(false)
  const [evalInfoOpen, setEvalInfoOpen] = useState(false)

  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const [evalResult, setEvalResult] = useState(null)
  const [evalLoading, setEvalLoading] = useState(false)
  const [evalError, setEvalError] = useState(null)
  const [evalSamples, setEvalSamples] = useState(30)
  const [evalStatus, setEvalStatus] = useState(null)
  const [evalProgress, setEvalProgress] = useState(null)
  const evalJobRef = useRef(null)
  const evalPollTimeoutRef = useRef(null)
  const evalStatusLabels = {
    queued: 'در صف پردازش',
    running: 'در حال پردازش',
    completed: 'تکمیل شد',
    failed: 'ناموفق',
  }
  const healthzUrl = API_BASE ? `${API_BASE}/healthz` : '/healthz'
  const serviceUrl = API_BASE || '/'
  const serviceLabel = API_BASE || 'همان مبدا'

  const endpoint = useMemo(() => {
    return API_BASE ? `${API_BASE}/api/summarize` : '/api/summarize'
  }, [])

  const evalAsyncEndpoint = useMemo(() => {
    return API_BASE ? `${API_BASE}/api/evaluate/async` : '/api/evaluate/async'
  }, [])

  const evalStatusEndpoint = useMemo(() => {
    return API_BASE ? `${API_BASE}/api/evaluate/status` : '/api/evaluate/status'
  }, [])

  useEffect(() => {
    return () => {
      if (evalPollTimeoutRef.current) {
        clearTimeout(evalPollTimeoutRef.current)
      }
    }
  }, [])

  const resetAbstractiveSettings = () => {
    setAbstractiveNumBeams(DEFAULT_ABSTRACTIVE_SETTINGS.numBeams)
    setAbstractiveLengthPenalty(DEFAULT_ABSTRACTIVE_SETTINGS.lengthPenalty)
    setAbstractiveRepetitionPenalty(DEFAULT_ABSTRACTIVE_SETTINGS.repetitionPenalty)
    setAbstractiveNoRepeatNgramSize(DEFAULT_ABSTRACTIVE_SETTINGS.noRepeatNgramSize)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setSummary(null)

    const length = levelToPercentage[summaryLevel]
    const outputLength = length

    const payload = {
      text,
      method,
      length: outputLength,
      ...(method === 'hybrid'
        ? {
            extractive_length: hybridExtractiveRatio,
            abstractive_length: outputLength,
          }
        : {}),
      ...(method === 'abstractive' || method === 'hybrid'
        ? {
            abstractive_num_beams: abstractiveNumBeams,
            abstractive_length_penalty: abstractiveLengthPenalty,
            abstractive_repetition_penalty: abstractiveRepetitionPenalty,
            abstractive_no_repeat_ngram_size: abstractiveNoRepeatNgramSize,
          }
        : {}),
    }



    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      })

      const data = await response.json()

      if (response.ok && data.ok) {
        setSummary(data)
      } else {
        setError(data?.error || 'خطا در دریافت خلاصه')
      }
    } catch {
      setError('خطا در ارتباط با سرور. مطمئن شوید سرویس‌ها در حال اجرا هستند.')
    } finally {
      setLoading(false)
    }
  }

  const handleEvaluate = async () => {
    setEvalLoading(true)
    setEvalError(null)
    setEvalResult(null)
    setEvalStatus('queued')
    setEvalProgress(null)
    evalJobRef.current = null
    if (evalPollTimeoutRef.current) {
      clearTimeout(evalPollTimeoutRef.current)
    }

    const payload = {
      method,
      length: levelToPercentage[summaryLevel],
      ...(method === 'hybrid'
        ? {
            extractive_length: hybridExtractiveRatio,
            abstractive_length: levelToPercentage[summaryLevel],
          }
        : {}),
      max_samples: evalSamples,
      ...(method === 'abstractive' || method === 'hybrid'
        ? {
            abstractive_num_beams: abstractiveNumBeams,
            abstractive_length_penalty: abstractiveLengthPenalty,
            abstractive_repetition_penalty: abstractiveRepetitionPenalty,
            abstractive_no_repeat_ngram_size: abstractiveNoRepeatNgramSize,
          }
        : {}),
    }

    try {
      const response = await fetch(evalAsyncEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      })

      const data = await response.json()

      if (response.ok && data?.job_id) {
        evalJobRef.current = data.job_id
        setEvalStatus(data.status || 'queued')
        pollEvalStatus(data.job_id)
      } else {
        setEvalError(data?.error || 'خطا در اجرای تست')
        setEvalLoading(false)
        setEvalStatus(null)
      }
    } catch {
      setEvalError('خطا در ارتباط با سرور. مطمئن شوید سرویس‌ها در حال اجرا هستند.')
      setEvalLoading(false)
      setEvalStatus(null)
    } finally {
      if (!evalJobRef.current) {
        setEvalLoading(false)
      }
    }
  }

  const pollEvalStatus = async (jobId) => {
    if (!jobId || evalJobRef.current !== jobId) {
      return
    }

    try {
      const response = await fetch(`${evalStatusEndpoint}/${jobId}`, {
        headers: { 'Content-Type': 'application/json' },
      })
      const data = await response.json()

      if (!response.ok) {
        setEvalError(data?.error || 'خطا در دریافت وضعیت تست')
        setEvalLoading(false)
        setEvalStatus(null)
        setEvalProgress(null)
        return
      }

      if (data?.progress) {
        setEvalProgress(data.progress)
      }

      if (data.status === 'completed') {
        setEvalResult(data.result)
        setEvalLoading(false)
        setEvalStatus('completed')
        setEvalProgress(data?.progress || null)
        return
      }

      if (data.status === 'failed') {
        setEvalError(data?.error || 'خطا در اجرای تست')
        setEvalLoading(false)
        setEvalStatus('failed')
        setEvalProgress(data?.progress || null)
        return
      }

      setEvalStatus(data.status)
      evalPollTimeoutRef.current = setTimeout(() => pollEvalStatus(jobId), 3000)
    } catch {
      setEvalError('خطا در ارتباط با سرور. مطمئن شوید سرویس‌ها در حال اجرا هستند.')
      setEvalLoading(false)
      setEvalStatus(null)
      setEvalProgress(null)
    }
  }

  return (
    <div className="min-h-screen px-4 py-10 lg:px-10" dir="rtl">
      <div className="mx-auto flex max-w-6xl flex-col gap-8">
        <header className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="glass-panel rounded-3xl p-8 lg:p-10">
           
            <h1 className="text-3xl font-black leading-tight text-[color:var(--ink-900)] lg:text-4xl">
             خلاصه‌سازی متون فارسی
              <span className="block text-[color:var(--accent-2)]">با کنترل کیفیت سازمانی</span>
            </h1>
           
           <br />
            <p className="mt-4 text-base leading-relaxed text-[color:var(--ink-500)]">
              انتخاب بین دو روش محلی و یک سرویس ابری، با کنترل طول، شفافیت در متریک‌ها و گزارش دقیق
              پردازش.
            </p>
           
          </div>
          <div className="card-surface rounded-3xl p-6 lg:p-8">
            <h2 className="text-xl font-bold text-[color:var(--ink-900)]">کنترل سریع</h2>
            <p className="mt-2 text-sm text-[color:var(--ink-500)]">
              متن نمونه را وارد کنید و روش مناسب را انتخاب کنید.
            </p>
            <button
              type="button"
              onClick={() => setText(exampleTextByLang["fa"])}
              className="mt-4 w-full rounded-2xl border border-[color:var(--accent-2)]/20 bg-[color:var(--accent-2)]/10 px-4 py-3 text-sm font-semibold text-[color:var(--accent-2)] transition hover:bg-[color:var(--accent-2)] hover:text-white"
            >
              درج متن نمونه
            </button>
            <div className="mt-6 grid gap-3 text-sm">
              <div className="rounded-2xl bg-[color:var(--surface)] px-4 py-3">
                <p className="text-xs text-[color:var(--ink-500)]">وضعیت API</p>
                <a
                  href={healthzUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="block w-full text-left font-semibold text-[color:var(--ink-900)] transition hover:text-[color:var(--accent-2)]"
                  dir="ltr"
                >
                  /healthz
                </a>
              </div>
              <div className="rounded-2xl bg-[color:var(--surface)] px-4 py-3">
                <p className="text-xs text-[color:var(--ink-500)]">آدرس سرویس</p>
                <a
                  href={serviceUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="block w-full break-all text-left font-semibold text-[color:var(--ink-900)] transition hover:text-[color:var(--accent-2)]"
                  dir="ltr"
                >
                  {serviceLabel}
                </a>
              </div>
            </div>
          </div>
        </header>

        <div className="card-surface rounded-3xl p-6 lg:p-10">
          <form onSubmit={handleSubmit} className="grid gap-8">
            <div>
              <label className="mb-3 block text-sm font-semibold text-[color:var(--ink-700)]">
                متن ورودی
              </label>
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                className="min-h-[200px] w-full rounded-3xl border border-transparent bg-[color:var(--surface)] p-4 text-base text-[color:var(--ink-900)] outline-none transition focus:border-[color:var(--accent-2)]/40 focus:ring-4 focus:ring-[color:var(--ring)]"
                placeholder= "متن خود را وارد کنید."
                dir="rtl"
                required
              />
            </div>

           
            <div>
              <label className="mb-4 block text-sm font-semibold text-[color:var(--ink-700)]">
                روش خلاصه‌سازی
              </label>
              <div className="grid gap-4 md:grid-cols-2">
                {methods.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => setMethod(item.id)}
                    className={`rounded-3xl border-2 p-4 text-right transition ${
                      method === item.id
                        ? 'border-[color:var(--accent-2)] bg-[color:var(--accent-2)]/10'
                        : 'border-transparent bg-[color:var(--surface)] hover:border-[color:var(--accent-2)]/40'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <h3 className="text-base font-bold text-[color:var(--ink-900)]">
                        {item.title}
                      </h3>
                      <span className="rounded-full bg-white px-3 py-1 text-[11px] font-semibold text-[color:var(--accent-2)]">
                        {item.tag}
                      </span>
                    </div>
                    <p className="mt-2 text-xs text-[color:var(--ink-500)]">{item.subtitle}</p>
                  </button>
                ))}
              </div>
            </div>

            <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
              {method === 'hybrid' ? (
                <div className="grid gap-4 rounded-3xl bg-[color:var(--surface)] p-5">
                  <div>
                    <label className="mb-2 block text-sm font-semibold text-[color:var(--ink-700)]">
                      نسبت مرحله استخراجی
                    </label>
                    <p className="text-xs text-[color:var(--ink-500)]">
                      درصد متن اولیه که برای مرحله مولد نگه داشته می‌شود.
                    </p>
                    <div className="mt-4 rounded-2xl bg-white px-4 py-4">
                      <div className="flex items-center justify-between text-xs font-semibold text-[color:var(--ink-600)]">
                        <span>کم</span>
                        <span>{hybridExtractiveRatio}%</span>
                        <span>زیاد</span>
                      </div>
                      <input
                        type="range"
                        min="10"
                        max="90"
                        step="5"
                        value={hybridExtractiveRatio}
                        onChange={(e) => setHybridExtractiveRatio(Number(e.target.value))}
                        className="mt-3 w-full accent-[color:var(--accent-2)]"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="mb-3 block text-sm font-semibold text-[color:var(--ink-700)]">
                      طول خروجی نهایی
                    </label>
                    <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
                      {Object.entries(levelToPercentage).map(([key, value]) => (
                        <label key={key} className="relative">
                          <input
                            type="radio"
                            value={key}
                            checked={summaryLevel === key}
                            onChange={(e) => setSummaryLevel(e.target.value)}
                            className="peer sr-only"
                          />
                          <div className="rounded-2xl border-2 border-transparent bg-white px-3 py-4 text-center text-sm font-semibold text-[color:var(--ink-700)] transition peer-checked:border-[color:var(--accent-2)] peer-checked:text-[color:var(--accent-2)]">
                            <div>
                              {key === 'very-short'
                                ? 'خیلی کوتاه'
                                : key === 'short'
                                ? 'کوتاه'
                                : key === 'medium'
                                ? 'متوسط'
                                : 'بلند'}
                            </div>
                            <div className="mt-2 text-xs text-[color:var(--ink-500)]">
                              {value}%
                            </div>
                          </div>
                        </label>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="rounded-3xl bg-[color:var(--surface)] p-5">
                  <label className="mb-3 block text-sm font-semibold text-[color:var(--ink-700)]">
                    طول خلاصه
                  </label>
                  <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
                    {Object.entries(levelToPercentage).map(([key, value]) => (
                      <label key={key} className="relative">
                        <input
                          type="radio"
                          value={key}
                          checked={summaryLevel === key}
                          onChange={(e) => setSummaryLevel(e.target.value)}
                          className="peer sr-only"
                        />
                        <div className="rounded-2xl border-2 border-transparent bg-white px-3 py-4 text-center text-sm font-semibold text-[color:var(--ink-700)] transition peer-checked:border-[color:var(--accent-2)] peer-checked:text-[color:var(--accent-2)]">
                          <div>
                            {key === 'very-short'
                              ? 'خیلی کوتاه'
                              : key === 'short'
                              ? 'کوتاه'
                              : key === 'medium'
                              ? 'متوسط'
                              : 'بلند'}
                          </div>
                          <div className="mt-2 text-xs text-[color:var(--ink-500)]">
                            {value}%
                          </div>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>
              )}

              <div className="rounded-3xl bg-[color:var(--surface)] p-5">
                <button
                  type="button"
                  onClick={() => setAbstractiveAdvancedOpen((prev) => !prev)}
                  className="flex w-full items-center justify-between text-sm font-semibold text-[color:var(--ink-700)]"
                  aria-expanded={abstractiveAdvancedOpen}
                  aria-controls="abstractive-advanced-panel"
                >
                  <span>تنظیمات حرفه‌ای</span>
                  <span className="text-xs text-[color:var(--ink-500)]">
                    {abstractiveAdvancedOpen ? 'بستن' : 'نمایش'}
                  </span>
                </button>
                {abstractiveAdvancedOpen && (
                  <div id="abstractive-advanced-panel" className="mt-4 grid gap-3">
                    {method === 'abstractive' || method === 'hybrid' ? (
                      <>
                        <p className="text-sm text-[color:var(--ink-500)]">
                          پارامترهای حرفه‌ای برای کنترل دقیق‌تر کیفیت و یکنواختی خروجی.
                        </p>
                        <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs text-amber-900">
                          این بخش فقط برای کاربرانی است که دقیقاً می‌دانند هر پارامتر چه اثری
                          دارد.
                        </div>
                        <label className="flex items-center gap-2 text-xs font-semibold text-[color:var(--ink-700)]">
                          <input
                            type="checkbox"
                            checked={abstractiveAdvancedEnabled}
                            onChange={(e) => setAbstractiveAdvancedEnabled(e.target.checked)}
                            className="h-4 w-4 accent-[color:var(--accent-2)]"
                          />
                          فعال‌سازی تنظیمات حرفه‌ای
                        </label>
                        <div className="flex items-center justify-between">
                          <p className="text-[11px] text-[color:var(--ink-500)]">
                            مقادیر پیشنهادی برای اکثر متن‌ها مناسب است.
                          </p>
                          <button
                            type="button"
                            onClick={resetAbstractiveSettings}
                            disabled={!abstractiveAdvancedEnabled}
                            className="rounded-full border border-[color:var(--accent-2)]/30 px-3 py-1 text-[11px] font-semibold text-[color:var(--accent-2)] transition hover:bg-[color:var(--accent-2)] hover:text-white disabled:cursor-not-allowed disabled:opacity-60"
                          >
                            ریست به پیش‌فرض
                          </button>
                        </div>
                        <div className="grid gap-3 md:grid-cols-2">
                          <div
                            className={`rounded-2xl bg-white p-3 ${
                              !abstractiveAdvancedEnabled ? 'opacity-60' : ''
                            }`}
                          >
                            <label className="block text-xs font-semibold text-[color:var(--ink-500)]">
                              تعداد پرتو (num_beams)
                            </label>
                            <input
                              type="number"
                              min="1"
                              max="8"
                              step="1"
                              value={abstractiveNumBeams}
                              onChange={(e) => {
                                const value = Number(e.target.value)
                                if (Number.isNaN(value)) return
                                setAbstractiveNumBeams(Math.min(8, Math.max(1, value)))
                              }}
                              disabled={!abstractiveAdvancedEnabled}
                              className="mt-2 w-full rounded-2xl border border-transparent bg-[color:var(--surface)] px-3 py-2 text-sm text-[color:var(--ink-900)] outline-none focus:border-[color:var(--accent-2)]/40"
                              dir="ltr"
                            />
                            <p className="mt-1 text-[11px] text-[color:var(--ink-500)]">
                              کیفیت بالاتر، سرعت کمتر
                            </p>
                          </div>
                          <div
                            className={`rounded-2xl bg-white p-3 ${
                              !abstractiveAdvancedEnabled ? 'opacity-60' : ''
                            }`}
                          >
                            <label className="block text-xs font-semibold text-[color:var(--ink-500)]">
                              جریمه طول (length_penalty)
                            </label>
                            <input
                              type="number"
                              min="0.2"
                              max="2.0"
                              step="0.05"
                              value={abstractiveLengthPenalty}
                              onChange={(e) => {
                                const value = Number(e.target.value)
                                if (Number.isNaN(value)) return
                                setAbstractiveLengthPenalty(
                                  Math.min(2.0, Math.max(0.2, value)),
                                )
                              }}
                              disabled={!abstractiveAdvancedEnabled}
                              className="mt-2 w-full rounded-2xl border border-transparent bg-[color:var(--surface)] px-3 py-2 text-sm text-[color:var(--ink-900)] outline-none focus:border-[color:var(--accent-2)]/40"
                              dir="ltr"
                            />
                            <p className="mt-1 text-[11px] text-[color:var(--ink-500)]">
                              مقدار بیشتر = خلاصه بلندتر
                            </p>
                          </div>
                          <div
                            className={`rounded-2xl bg-white p-3 ${
                              !abstractiveAdvancedEnabled ? 'opacity-60' : ''
                            }`}
                          >
                            <label className="block text-xs font-semibold text-[color:var(--ink-500)]">
                              جریمه تکرار (repetition_penalty)
                            </label>
                            <input
                              type="number"
                              min="1.0"
                              max="2.0"
                              step="0.05"
                              value={abstractiveRepetitionPenalty}
                              onChange={(e) => {
                                const value = Number(e.target.value)
                                if (Number.isNaN(value)) return
                                setAbstractiveRepetitionPenalty(
                                  Math.min(2.0, Math.max(1.0, value)),
                                )
                              }}
                              disabled={!abstractiveAdvancedEnabled}
                              className="mt-2 w-full rounded-2xl border border-transparent bg-[color:var(--surface)] px-3 py-2 text-sm text-[color:var(--ink-900)] outline-none focus:border-[color:var(--accent-2)]/40"
                              dir="ltr"
                            />
                            <p className="mt-1 text-[11px] text-[color:var(--ink-500)]">
                              مقدار بیشتر = تکرار کمتر
                            </p>
                          </div>
                          <div
                            className={`rounded-2xl bg-white p-3 ${
                              !abstractiveAdvancedEnabled ? 'opacity-60' : ''
                            }`}
                          >
                            <label className="block text-xs font-semibold text-[color:var(--ink-500)]">
                              عدم تکرار n-gram (no_repeat_ngram_size)
                            </label>
                            <input
                              type="number"
                              min="0"
                              max="6"
                              step="1"
                              value={abstractiveNoRepeatNgramSize}
                              onChange={(e) => {
                                const value = Number(e.target.value)
                                if (Number.isNaN(value)) return
                                setAbstractiveNoRepeatNgramSize(
                                  Math.min(6, Math.max(0, value)),
                                )
                              }}
                              disabled={!abstractiveAdvancedEnabled}
                              className="mt-2 w-full rounded-2xl border border-transparent bg-[color:var(--surface)] px-3 py-2 text-sm text-[color:var(--ink-900)] outline-none focus:border-[color:var(--accent-2)]/40"
                              dir="ltr"
                            />
                            <p className="mt-1 text-[11px] text-[color:var(--ink-500)]">
                              مقدار بالاتر = جلوگیری از تکرار بیشتر
                            </p>
                          </div>
                        </div>
                      </>
                    ) : (
                      <p className="text-sm text-[color:var(--ink-500)]">
                        این روش به صورت مستقیم اجرا می‌شود و کنترل‌های ویژه ندارد.
                      </p>
                    )}
                  </div>
                )}
              </div>
            </div>

           
            <button
              type="submit"
              disabled={loading || !text.trim()}
              className="w-full rounded-3xl bg-[color:var(--accent-2)] px-6 py-4 text-base font-bold text-white transition hover:bg-[#163a5e] disabled:cursor-not-allowed disabled:bg-gray-400"
            >
              {loading ? 'در حال پردازش...' : 'اجرای خلاصه‌سازی'}
            </button>
          </form>
        </div>

        {error && (
          <div className="card-surface rounded-3xl border border-red-200 bg-red-50 p-5 text-red-700">
            {error}
          </div>
        )}

        {summary && (
          <div className="card-surface rounded-3xl p-6 lg:p-8">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h2 className="text-2xl font-bold text-[color:var(--ink-900)]">خلاصه نهایی</h2>
                <p className="mt-1 text-sm text-[color:var(--ink-500)]">
                  درخواست #{summary.request_id}
                </p>
              </div>
              <span className="rounded-full bg-[color:var(--accent-2)]/10 px-4 py-2 text-xs font-semibold text-[color:var(--accent-2)]">
                {summary.method.toUpperCase()}
              </span>
            </div>

            <div
              className="mt-5 rounded-3xl bg-[color:var(--surface)] p-5 text-[color:var(--ink-900)]"
              dir="rtl"
            >
              <p className="leading-relaxed">{summary.summary}</p>
            </div>

            <div className="mt-6 grid gap-4 md:grid-cols-4">
              <div className="rounded-2xl bg-white p-4 text-center">
                <p className="text-xs text-[color:var(--ink-500)]">جملات اصلی</p>
                <p className="text-lg font-semibold text-[color:var(--ink-900)]">
                  {summary.original_length_sentences ?? '—'}
                </p>
              </div>
              <div className="rounded-2xl bg-white p-4 text-center">
                <p className="text-xs text-[color:var(--ink-500)]">جملات خلاصه</p>
                <p className="text-lg font-semibold text-[color:var(--ink-900)]">
                  {summary.summary_length_sentences ?? '—'}
                </p>
              </div>
              <div className="rounded-2xl bg-white p-4 text-center">
                <p className="text-xs text-[color:var(--ink-500)]">زمان پردازش</p>
                <p className="text-lg font-semibold text-[color:var(--ink-900)]">
                  {summary.processing_time_sec}s
                </p>
              </div>
              <div className="rounded-2xl bg-white p-4 text-center">
                <p className="text-xs text-[color:var(--ink-500)]">نسبت خلاصه</p>
                <p className="text-lg font-semibold text-[color:var(--ink-900)]">
                  {summary.extra?.metrics?.requested_abstractive_ratio
                    ? `${Math.round(summary.extra.metrics.requested_abstractive_ratio * 100)}%`
                    : summary.extra?.metrics?.requested_length_ratio
                    ? `${Math.round(summary.extra.metrics.requested_length_ratio * 100)}%`
                    : '—'}
                </p>
              </div>
            </div>
          </div>
        )}

        <div className="card-surface rounded-3xl p-6 lg:p-8">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h2 className="text-2xl font-bold text-[color:var(--ink-900)]">حالت تست دیتاست</h2>
            </div>
            <button
              type="button"
              onClick={() => setEvalInfoOpen((prev) => !prev)}
              className="rounded-full border border-[color:var(--accent-2)]/30 px-4 py-2 text-xs font-semibold text-[color:var(--accent-2)] transition hover:bg-[color:var(--accent-2)] hover:text-white"
              aria-expanded={evalInfoOpen}
              aria-controls="evaluation-info-panel"
            >
              {evalInfoOpen ? 'بستن توضیحات امتیازها' : 'نمایش توضیحات امتیازها'}
            </button>
            <span className="rounded-full bg-[color:var(--accent-2)]/10 px-4 py-2 text-xs font-semibold text-[color:var(--accent-2)]">
              {method.toUpperCase()}
            </span>
          </div>
          {evalInfoOpen && (
            <div id="evaluation-info-panel" className="mt-4 grid gap-3 text-xs text-[color:var(--ink-500)]">
              <p>
                برای ارزیابی کیفیت خلاصه‌سازی، از معیارهای ROUGE استفاده می‌شود. در روش‌های
                extractive مبتنی بر TextRank که جملات مستقیماً از متن اصلی انتخاب می‌شوند،
                معمولاً انتظار می‌رود امتیازها در بازه‌های زیر قرار گیرند:
              </p>
              <p>ROUGE-1 F1: حدود 0.20 تا 0.30</p>
              <p>ROUGE-2 F1: حدود 0.08 تا 0.15</p>
              <p>ROUGE-L F1: حدود 0.15 تا 0.25</p>
              <p>
                این بازه‌ها نشان‌دهنده عملکرد مناسب برای روش‌های بدون آموزش یا مبتنی بر گراف
                هستند و مقادیر بالاتر معمولاً نیازمند استفاده از مدل‌های معنایی عمیق‌تر است.
              </p>
              <p>
                در مقابل، در روش‌های abstractive که خلاصه به‌صورت مولد و با بازنویسی محتوا
                تولید می‌شود، به دلیل انعطاف زبانی بیشتر، معمولاً امتیازهای بالاتری گزارش
                می‌شود:
              </p>
              <p>ROUGE-1 F1: حدود 0.30 تا 0.45</p>
              <p>ROUGE-2 F1: حدود 0.15 تا 0.30</p>
              <p>ROUGE-L F1: حدود 0.25 تا 0.40</p>
              <p>
                در روش ترکیبی (Hybrid)، انتظار می‌رود خروجی بین دو بازه بالا قرار بگیرد و به
                تنظیم طول دو مرحله وابسته است. به‌صورت تقریبی:
              </p>
              <p>ROUGE-1 F1: حدود 0.25 تا 0.40</p>
              <p>ROUGE-2 F1: حدود 0.10 تا 0.22</p>
              <p>ROUGE-L F1: حدود 0.20 تا 0.32</p>
            </div>
          )}

          <div className="mt-6 grid gap-4 md:grid-cols-3">
            <div className="rounded-2xl bg-[color:var(--surface)] p-4">
              <label className="block text-xs font-semibold text-[color:var(--ink-500)]">
                تعداد نمونه
              </label>
              <input
                type="number"
                min="1"
                max="1000"
                value={evalSamples}
                onChange={(e) => setEvalSamples(Number(e.target.value))}
                className="mt-2 w-full rounded-2xl border border-transparent bg-white px-3 py-2 text-sm text-[color:var(--ink-900)] outline-none focus:border-[color:var(--accent-2)]/40"
              />
            </div>
            <div className="rounded-2xl bg-[color:var(--surface)] p-4">
              <p className="text-xs text-[color:var(--ink-500)]">طول خلاصه</p>
              <p className="mt-2 text-lg font-semibold text-[color:var(--ink-900)]">
                {method === 'hybrid'
                  ? `${levelToPercentage[summaryLevel]}%`
                  : `${levelToPercentage[summaryLevel]}%`}
              </p>
            </div>
            <div className="rounded-2xl bg-[color:var(--surface)] p-4">
              <p className="text-xs text-[color:var(--ink-500)]">روش انتخاب‌شده</p>
              <p className="mt-2 text-lg font-semibold text-[color:var(--ink-900)]">
                {method === 'extractive'
                  ? 'استخراجی'
                  : method === 'abstractive'
                  ? 'مولد'
                  : 'ترکیبی'}
              </p>
            </div>
            {method === 'hybrid' && (
              <div className="rounded-2xl bg-[color:var(--surface)] p-4">
                <p className="text-xs text-[color:var(--ink-500)]">نسبت استخراجی</p>
                <p className="mt-2 text-lg font-semibold text-[color:var(--ink-900)]">
                  {hybridExtractiveRatio}%
                </p>
              </div>
            )}
          </div>

          <button
            type="button"
            onClick={handleEvaluate}
            disabled={evalLoading}
            className="mt-6 w-full rounded-3xl bg-[color:var(--accent-2)] px-6 py-4 text-base font-bold text-white transition hover:bg-[#163a5e] disabled:cursor-not-allowed disabled:bg-gray-400"
          >
            {evalLoading ? 'در حال اجرای تست...' : 'اجرای ارزیابی'}
          </button>

          {evalLoading && evalStatus && (
            <div className="mt-4 rounded-2xl bg-[color:var(--surface)] p-4 text-sm text-[color:var(--ink-500)]">
              وضعیت ارزیابی: {evalStatusLabels[evalStatus] || evalStatus}
            </div>
          )}

          {evalLoading && evalProgress && (
            <div className="mt-3 rounded-2xl bg-[color:var(--surface)] p-4 text-sm text-[color:var(--ink-500)]">
              {evalProgress.total
                ? `پیشرفت: ${evalProgress.processed} از ${evalProgress.total} (${evalProgress.percent ?? 0}%)`
                : `پیشرفت: ${evalProgress.processed}`}
              {typeof evalProgress.samples === 'number' && (
                <span className="ml-2">
                  (نمونه‌های معتبر: {evalProgress.samples} | رد شده: {evalProgress.skipped})
                </span>
              )}
            </div>
          )}

          {evalError && (
            <div className="mt-4 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              {evalError}
            </div>
          )}

          {evalResult && (
            <div className="mt-6 grid gap-4">
              <div className="grid gap-4 md:grid-cols-3">
                <div className="rounded-2xl bg-white p-4 text-center">
                  <p className="text-xs text-[color:var(--ink-500)]">طول میانگین خروجی</p>
                  <p className="text-lg font-semibold text-[color:var(--ink-900)]">
                    {evalResult.avg_gen_len}
                  </p>
                </div>
                <div className="rounded-2xl bg-white p-4 text-center">
                  <p className="text-xs text-[color:var(--ink-500)]">طول میانگین مرجع</p>
                  <p className="text-lg font-semibold text-[color:var(--ink-900)]">
                    {evalResult.avg_ref_len}
                  </p>
                </div>
                <div className="rounded-2xl bg-white p-4 text-center">
                  <p className="text-xs text-[color:var(--ink-500)]">نسبت فشرده‌سازی</p>
                  <p className="text-lg font-semibold text-[color:var(--ink-900)]">
                    {evalResult.compression_ratio}
                  </p>
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-3">
                <div className="rounded-2xl bg-[color:var(--surface)] p-4">
                  <p className="text-xs uppercase text-[color:var(--ink-500)]">ROUGE-1 F1</p>
                  <p className="mt-2 text-lg font-semibold text-[color:var(--ink-900)]">
                    {evalResult.rouge1_f1 ?? '—'}
                  </p>
                </div>
                <div className="rounded-2xl bg-[color:var(--surface)] p-4">
                  <p className="text-xs uppercase text-[color:var(--ink-500)]">ROUGE-2 F1</p>
                  <p className="mt-2 text-lg font-semibold text-[color:var(--ink-900)]">
                    {evalResult.rouge2_f1 ?? '—'}
                  </p>
                </div>
                <div className="rounded-2xl bg-[color:var(--surface)] p-4">
                  <p className="text-xs uppercase text-[color:var(--ink-500)]">ROUGE-L F1</p>
                  <p className="mt-2 text-lg font-semibold text-[color:var(--ink-900)]">
                    {evalResult.rougeL_f1 ?? '—'}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default App
