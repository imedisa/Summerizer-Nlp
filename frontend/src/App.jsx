import { useState } from 'react'

function App() {
  const [text, setText] = useState('')
  const [method, setMethod] = useState('extractive')
  const [summaryLevel, setSummaryLevel] = useState('medium') // تغییر از length به summaryLevel
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // تبدیل سطح به درصد
  const levelToPercentage = {
    'very-short': 20,
    'short': 35,
    'medium': 50,
    'long': 70
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setSummary(null)

    const length = levelToPercentage[summaryLevel]

    try {
      const response = await fetch('http://127.0.0.1:8000/api/summarize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text, method, length }),
      })

      const data = await response.json()

      if (response.ok) {
        setSummary(data)
      } else {
        setError('خطا در دریافت خلاصه')
      }
    } catch {
      setError('خطا در ارتباط با سرور. مطمئن شوید Backend در حال اجراست.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-linear-to-br from-blue-50 to-indigo-100 py-8 px-4" dir="rtl">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            سامانه خلاصه‌سازی متن فارسی
          </h1>
          <p className="text-gray-600">با استفاده از الگوریتم‌های TextRank و هوش مصنوعی</p>
        </div>

        {/* Form */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <form onSubmit={handleSubmit}>
            {/* Text Area */}
            <div className="mb-4">
              <label className="block text-gray-700 font-semibold mb-2">
                متن ورودی:
              </label>
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                className="w-full h-40 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="متن فارسی خود را اینجا وارد کنید..."
                required
              />
            </div>

            {/* Method Selection */}
            <div className="mb-4">
              <label className="block text-gray-700 font-semibold mb-2">
                روش خلاصه‌سازی:
              </label>
              <div className="flex gap-4">
                <label className="flex items-center cursor-pointer">
                  <input
                    type="radio"
                    value="extractive"
                    checked={method === 'extractive'}
                    onChange={(e) => setMethod(e.target.value)}
                    className="ml-2"
                  />
                  <span>استخراجی (TextRank)</span>
                </label>
                <label className="flex items-center cursor-pointer">
                  <input
                    type="radio"
                    value="abstractive"
                    checked={method === 'abstractive'}
                    onChange={(e) => setMethod(e.target.value)}
                    className="ml-2"
                  />
                  <span>مولد (AI)</span>
                </label>
              </div>
            </div>

            {/* Summary Level Selection - جدید */}
            <div className="mb-6">
              <label className="block text-gray-700 font-semibold mb-3">
                طول خلاصه:
              </label>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <label className="relative cursor-pointer">
                  <input
                    type="radio"
                    value="very-short"
                    checked={summaryLevel === 'very-short'}
                    onChange={(e) => setSummaryLevel(e.target.value)}
                    className="peer sr-only"
                  />
                  <div className="p-4 border-2 border-gray-300 rounded-lg text-center transition-all peer-checked:border-indigo-600 peer-checked:bg-indigo-50 peer-checked:text-indigo-700 hover:border-indigo-400">
                    <div className="font-semibold">خیلی کوتاه</div>
                    <div className="text-xs text-gray-500 mt-1">20%</div>
                  </div>
                </label>

                <label className="relative cursor-pointer">
                  <input
                    type="radio"
                    value="short"
                    checked={summaryLevel === 'short'}
                    onChange={(e) => setSummaryLevel(e.target.value)}
                    className="peer sr-only"
                  />
                  <div className="p-4 border-2 border-gray-300 rounded-lg text-center transition-all peer-checked:border-indigo-600 peer-checked:bg-indigo-50 peer-checked:text-indigo-700 hover:border-indigo-400">
                    <div className="font-semibold">کوتاه</div>
                    <div className="text-xs text-gray-500 mt-1">35%</div>
                  </div>
                </label>

                <label className="relative cursor-pointer">
                  <input
                    type="radio"
                    value="medium"
                    checked={summaryLevel === 'medium'}
                    onChange={(e) => setSummaryLevel(e.target.value)}
                    className="peer sr-only"
                  />
                  <div className="p-4 border-2 border-gray-300 rounded-lg text-center transition-all peer-checked:border-indigo-600 peer-checked:bg-indigo-50 peer-checked:text-indigo-700 hover:border-indigo-400">
                    <div className="font-semibold">متوسط</div>
                    <div className="text-xs text-gray-500 mt-1">50%</div>
                  </div>
                </label>

                <label className="relative cursor-pointer">
                  <input
                    type="radio"
                    value="long"
                    checked={summaryLevel === 'long'}
                    onChange={(e) => setSummaryLevel(e.target.value)}
                    className="peer sr-only"
                  />
                  <div className="p-4 border-2 border-gray-300 rounded-lg text-center transition-all peer-checked:border-indigo-600 peer-checked:bg-indigo-50 peer-checked:text-indigo-700 hover:border-indigo-400">
                    <div className="font-semibold">بلند</div>
                    <div className="text-xs text-gray-500 mt-1">70%</div>
                  </div>
                </label>
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading || !text.trim()}
              className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-3 rounded-lg transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {loading ? 'در حال پردازش...' : 'خلاصه‌سازی متن'}
            </button>
          </form>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {/* Summary Result */}
        {summary && (
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">خلاصه متن:</h2>
            <div className="bg-gray-50 p-4 rounded-lg mb-4">
              <p className="text-gray-800 leading-relaxed">{summary.summary}</p>
            </div>

            {/* Statistics */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
              <div className="bg-blue-50 p-3 rounded">
                <p className="text-sm text-gray-600">روش</p>
                <p className="font-semibold text-gray-800">{summary.method}</p>
              </div>
              <div className="bg-green-50 p-3 rounded">
                <p className="text-sm text-gray-600">جملات اصلی</p>
                <p className="font-semibold text-gray-800">{summary.original_length_sentences}</p>
              </div>
              <div className="bg-yellow-50 p-3 rounded">
                <p className="text-sm text-gray-600">جملات خلاصه</p>
                <p className="font-semibold text-gray-800">{summary.summary_length_sentences}</p>
              </div>
              <div className="bg-purple-50 p-3 rounded">
                <p className="text-sm text-gray-600">زمان پردازش</p>
                <p className="font-semibold text-gray-800">{summary.processing_time_sec}s</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
