/**
 * AskBoardPack.jsx
 *
 * Natural-language Q&A over the board pack, backed by a genuine tool-calling
 * agent (see backend/app/routers/chat.py) rather than a single prompt-stuffed
 * call. Each answer's tool calls are shown inline — the audit trail is the
 * feature, not an afterthought.
 */
import React, { useEffect, useRef, useState } from 'react'
import { api } from '../api'
import { SectionHeading, DisclosureBanner, Panel } from './ui.jsx'

const SUGGESTED_QUESTIONS = [
  'How has our customer concentration changed since FY2024?',
  'Why is there no EBITDA figure anywhere in this report?',
  'What actually happened to cash vs what we projected after the placement?',
  'How exposed are we to Ireland vs international revenue?',
]

function ToolCallChip({ call }) {
  const argStr = Object.keys(call.input).length
    ? `(${Object.entries(call.input).map(([k, v]) => `${k}=${v}`).join(', ')})`
    : '()'
  return (
    <span className="tool-chip">
      <span className="tool-chip-dot" />
      {call.tool}{argStr}
    </span>
  )
}

function Message({ role, content, toolCalls, isError }) {
  if (role === 'user') {
    return <div className="chat-msg chat-msg-user">{content}</div>
  }
  return (
    <div className={`chat-msg chat-msg-assistant ${isError ? 'chat-msg-error' : ''}`}>
      <div className="chat-msg-body">{content}</div>
      {toolCalls && toolCalls.length > 0 && (
        <div className="tool-chip-row">
          <span className="tool-chip-label">Data queried:</span>
          {toolCalls.map((c, i) => <ToolCallChip key={i} call={c} />)}
        </div>
      )}
    </div>
  )
}

export function AskBoardPack() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const scrollRef = useRef(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, loading])

  async function send(question) {
    const q = (question ?? input).trim()
    if (!q || loading) return

    const history = messages.map((m) => ({ role: m.role, content: m.content }))
    setMessages((prev) => [...prev, { role: 'user', content: q }])
    setInput('')
    setLoading(true)

    try {
      const res = await api.chat(q, history)
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: res.answer, toolCalls: res.tool_calls, generatedBy: res.generated_by },
      ])
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: err.message, isError: true },
      ])
    } finally {
      setLoading(false)
    }
  }

  function handleSubmit(e) {
    e.preventDefault()
    send()
  }

  return (
    <>
      <SectionHeading eyebrow="Section 07" title="Ask the Board Pack" />
      <DisclosureBanner>
        This isn't a single prompt with the whole dataset stuffed in — each question
        triggers Claude to call specific database queries (visible below every answer
        as "Data queried"), so you can see exactly what grounded the response. Without
        <code style={{ margin: '0 4px' }}>ANTHROPIC_API_KEY</code> configured, a small
        set of common questions (revenue, cash, EBITDA) still work via keyword fallback.
      </DisclosureBanner>

      <Panel>
        <div className="chat-window" ref={scrollRef}>
          {messages.length === 0 && (
            <div className="chat-empty">
              <p className="chat-empty-title">Ask anything about the board pack.</p>
              <div className="chat-suggestions">
                {SUGGESTED_QUESTIONS.map((q, i) => (
                  <button key={i} className="chat-suggestion" onClick={() => send(q)}>
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((m, i) => <Message key={i} {...m} />)}

          {loading && (
            <div className="chat-msg chat-msg-assistant chat-msg-loading">
              Querying the board pack…
            </div>
          )}
        </div>

        <form className="chat-input-row" onSubmit={handleSubmit}>
          <input
            className="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="e.g. Why did cash come in lower than the pro-forma estimate?"
            disabled={loading}
          />
          <button className="chat-send-btn" type="submit" disabled={loading || !input.trim()}>
            Ask
          </button>
        </form>
      </Panel>
    </>
  )
}
