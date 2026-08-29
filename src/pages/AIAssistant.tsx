import { useState, useRef, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import {
  Send, Mic, MicOff, Brain, FileText, Image, Upload,
  Copy, ThumbsUp, ThumbsDown, Settings, History, RefreshCw
} from 'lucide-react'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { ScrollArea } from '../components/ui/ScrollArea'
import { cn } from '../utils/helpers'

const WELCOME_MESSAGE = `Welcome to MedFusion AI Assistant. I can help you with:

• **Multimodal clinical reasoning** — Fuse ECG, imaging, labs, and notes
• **Differential diagnosis** — Evidence-based suggestions from MIMIC-IV cohorts
• **Guideline lookup** — ESC, ACC, AHA, KDIGO, Surviving Sepsis
• **Study interpretation** — CXR, CT, MRI, PET, Echo findings
• **Risk stratification** — CHA₂DS₂-VASc, GRACE, CURB-65, SOFA, etc.
• **Medication review** — Interactions, dosing, renal adjustment

**Important**: I am an AI assistant for clinical decision support only. All outputs require physician verification. Not a medical device.`

const QUICK_ACTIONS = [
  { label: 'Summarize patient', prompt: 'Summarize this patient\'s clinical picture including active problems, medications, recent labs, and imaging findings.' },
  { label: 'Differential diagnosis', prompt: 'Generate a prioritized differential diagnosis for the primary complaint based on available evidence.' },
  { label: 'Risk scores', prompt: 'Calculate relevant risk scores (CHA₂DS₂-VASc, GRACE, SOFA, CURB-65) for this patient.' },
  { label: 'Guideline check', prompt: 'Check current guideline recommendations for the patient\'s primary diagnosis.' },
  { label: 'Drug interactions', prompt: 'Review current medications for interactions, duplicates, and renal/hepatic dosing adjustments.' },
  { label: 'Imaging correlation', prompt: 'Correlate imaging findings with clinical presentation and lab data.' },
]

type Message = {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  citations?: { source: string; modality: string; excerpt: string }[]
  attachments?: { type: 'image' | 'file'; name: string; data: string }[]
}

export function AIAssistant() {
  const { patientId } = useParams<{ patientId: string }>()
  const [messages, setMessages] = useState<Message[]>([
    { id: '1', role: 'assistant', content: WELCOME_MESSAGE, timestamp: new Date() }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showQuickActions, setShowQuickActions] = useState(true)
  const [attachments, setAttachments] = useState<{ type: 'image' | 'file'; name: string; data: string }[]>([])
  const [voiceActive, setVoiceActive] = useState(false)
  const scrollRef = useRef<any>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() && attachments.length === 0) return
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
      attachments: [...attachments],
    }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setAttachments([])
    setShowQuickActions(false)
    setIsLoading(true)

    // Simulate AI response
    await new Promise(r => setTimeout(r, 1500))
    const response = generateResponse(input, patientId)
    setMessages(prev => [...prev, { ...response, id: (Date.now() + 1).toString() }])
    setIsLoading(false)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleVoice = () => {
    setVoiceActive(!voiceActive)
    // In real app: start Web Speech API or Whisper integration
  }

  const handleAttachment = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    files.forEach(file => {
      const reader = new FileReader()
      reader.onload = () => {
        setAttachments(prev => [...prev, {
          type: file.type.startsWith('image/') ? 'image' : 'file',
          name: file.name,
          data: reader.result as string,
        }])
      }
      reader.readAsDataURL(file)
    })
  }

  const useQuickAction = (prompt: string) => {
    setInput(prompt)
    handleSend()
  }

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 lg:p-6 border-b border-neutral-200 dark:border-neutral-800">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
          <div>
            <h2 className="text-2xl font-bold">AI clinical assistant</h2>
            <p className="text-neutral-500 text-sm">Multimodal reasoning · Evidence citations · Guideline-aware · Not a medical device</p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" leftIcon={<History className="h-4 w-4" />}>History</Button>
            <Button variant="outline" leftIcon={<Settings className="h-4 w-4" />}>Settings</Button>
          </div>
        </div>

        {showQuickActions && messages.length <= 1 && (
          <div className="flex flex-wrap gap-2">
            {QUICK_ACTIONS.map(a => (
              <Button
                key={a.label}
                variant="outline"
                size="sm"
                onClick={() => useQuickAction(a.prompt)}
                className="whitespace-nowrap"
              >
                {a.label}
              </Button>
            ))}
          </div>
        )}
      </div>

      <div className="flex-1 overflow-hidden flex flex-col">
        <ScrollArea className="flex-1 p-4 lg:p-6 space-y-6" ref={scrollRef}>
          {messages.map(msg => (
            <MessageBubble key={msg.id} message={msg} />
          ))}
          {isLoading && (
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-full bg-gradient-clinical flex items-center justify-center flex-shrink-0">
                <Brain className="h-4 w-4 text-white" />
              </div>
              <div className="flex-1">
                <div className="flex gap-1">
                  <TypingDot delay={0} />
                  <TypingDot delay={150} />
                  <TypingDot delay={300} />
                </div>
              </div>
            </div>
          )}
        </ScrollArea>

        <div className="border-t border-neutral-200 dark:border-neutral-800 p-4 bg-white/50 dark:bg-neutral-900/50 backdrop-blur-sm">
          <div className="flex items-end gap-3">
            <div className="relative flex-1">
              {attachments.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-2">
                  {attachments.map((a, i) => (
                    <Badge key={i} variant="info" className="gap-1">
                      {a.type === 'image' ? <Image className="h-3 w-3" /> : <FileText className="h-3 w-3" />}
                      {a.name}
                    </Badge>
                  ))}
                </div>
              )}
              <div className="relative">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask a clinical question, request a summary, or paste a note..."
                  className="w-full min-h-[56px] max-h-48 px-4 py-3 pr-14 text-sm rounded-xl border border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800 focus:border-medical-500 focus:ring-2 focus:ring-medical-500/20 resize-none"
                  rows={1}
                />
                <div className="absolute right-3 bottom-3 flex items-center gap-1">
                  <input type="file" id="file-upload" onChange={handleAttachment} className="hidden" multiple accept="image/*,.pdf,.txt,.json,.dicom,.dcm" />
                  <label htmlFor="file-upload" className="p-2 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-800 text-neutral-500" title="Attach file/image">
                    <Upload className="h-4 w-4" />
                  </label>
                  <button
                    onClick={handleVoice}
                    className={cn('p-2 rounded-lg text-neutral-500 transition-colors', voiceActive ? 'bg-critical-100 text-critical-600' : 'hover:bg-neutral-100 dark:hover:bg-neutral-800')}
                    title={voiceActive ? 'Stop voice input' : 'Start voice input'}
                  >
                    {voiceActive ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
                  </button>
                </div>
              </div>
            </div>
            <Button
              onClick={handleSend}
              disabled={!input.trim() && attachments.length === 0 || isLoading}
              size="lg"
              className="h-12"
            >
              {isLoading ? <Brain className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
            </Button>
          </div>
          <p className="text-xs text-neutral-400 mt-2 text-center">
            Enter to send · Shift+Enter for new line · Voice uses Web Speech API (Chrome/Edge)
          </p>
        </div>
      </div>
    </div>
  )
}

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user'
  const isSystem = message.role === 'system'

  return (
    <div className={cn('flex gap-3', isUser && 'flex-row-reverse')}>
      <div className={cn('w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0', isUser ? 'bg-neutral-200 dark:bg-neutral-700' : 'bg-gradient-clinical')}>
        {isUser ? (
          <span className="text-xs font-semibold text-neutral-600 dark:text-neutral-300">Dr</span>
        ) : (
          <Brain className="h-4 w-4 text-white" />
        )}
      </div>
      <div className={cn('flex-1 max-w-[80%]', isUser && 'text-right')}>
        <div className={cn(
          'inline-block px-4 py-3 rounded-2xl text-sm leading-relaxed',
          isUser
            ? 'bg-medical-500 text-white rounded-tr-none'
            : isSystem
            ? 'bg-neutral-100 dark:bg-neutral-800 rounded-bl-none text-neutral-700 dark:text-neutral-300'
            : 'bg-neutral-100 dark:bg-neutral-800 rounded-tl-none text-neutral-900 dark:text-neutral-100'
        )}>
          <div className="prose prose-sm dark:prose-invert max-w-none whitespace-pre-wrap">{message.content}</div>
          {message.citations && message.citations.length > 0 && (
            <details className="mt-3">
              <summary className="text-xs text-neutral-500 cursor-pointer flex items-center gap-1">
                <FileText className="h-3 w-3" />
                Citations ({message.citations.length})
              </summary>
              <ul className="mt-2 space-y-1 text-xs text-neutral-500">
                {message.citations.map((c, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <Badge size="sm" variant={c.modality === 'ecg' ? 'critical' : c.modality === 'imaging' ? 'medical' : 'vital'}>{c.modality}</Badge>
                    <span className="font-mono">{c.source}</span>
                    <span>— {c.excerpt}</span>
                  </li>
                ))}
              </ul>
            </details>
          )}
          {message.attachments && message.attachments.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {message.attachments.map((a, i) => (
                <Badge key={i} size="sm" variant="info" className="gap-1">
                  {a.type === 'image' ? <Image className="h-3 w-3" /> : <FileText className="h-3 w-3" />}
                  {a.name}
                </Badge>
              ))}
            </div>
          )}
        </div>
        <div className="flex items-center gap-2 mt-1 justify-end">
          <span className="text-[10px] text-neutral-400">{message.timestamp.toLocaleTimeString()}</span>
          {!isUser && (
            <>
              <Button variant="ghost" size="icon" className="h-6 w-6 p-0" title="Copy">
                <Copy className="h-3.5 w-3.5" />
              </Button>
              <Button variant="ghost" size="icon" className="h-6 w-6 p-0" title="Regenerate">
                <RefreshCw className="h-3.5 w-3.5" />
              </Button>
              <Button variant="ghost" size="icon" className="h-6 w-6 p-0" title="Helpful">
                <ThumbsUp className="h-3.5 w-3.5" />
              </Button>
              <Button variant="ghost" size="icon" className="h-6 w-6 p-0" title="Not helpful">
                <ThumbsDown className="h-3.5 w-3.5" />
              </Button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

function TypingDot({ delay }: { delay: number }) {
  return (
    <div
      className="w-2 h-2 bg-neutral-400 rounded-full animate-bounce"
      style={{ animationDelay: `${delay}ms` }}
    />
  )
}

function generateResponse(input: string, patientId?: string): Omit<Message, 'id'> {
  const lowerInput = input.toLowerCase()
  let content = ''
  const citations: Message['citations'] = []

  if (lowerInput.includes('summarize') || lowerInput.includes('summary')) {
    content = `**Patient Summary** (${patientId ? `ID: ${patientId}` : 'All patients'})

**Active Problems:**
• Heart failure with reduced EF (HFrEF)
• Atrial fibrillation
• Hyperkalemia (K+ 6.2)
• Acute kidney injury

**Current Medications:**
• Furosemide 40mg IV q12h
• Lisinopril 10mg daily (held)
• Apixaban 5mg BID
• Insulin glargine 24 units daily

**Recent Critical Labs:**
• K+ 6.2 mmol/L (critical high) — 2h ago
• Creatinine 2.8 mg/dL (high) — 2h ago
• Troponin 0.45 ng/mL (high) — 6h ago
• BNP 1,240 pg/mL (critical high) — 6h ago

**Imaging:** Portable CXR 4h ago — pulmonary vascular congestion, no effusion

**AI Assessment:** Acute decompensated heart failure with volume overload, hyperkalemia limiting GDMT, possible demand ischemia. Urgent diuresis and K+ management indicated.

*Confidence: 87% — Based on MIMIC-IV cohort matching (n=2,847 similar presentations)*`

    citations.push(
      { source: 'MIMIC-IV v2.2', modality: 'clinical', excerpt: 'ADHF cohort mortality 12.3% at 30 days' },
      { source: 'PTB-XL', modality: 'ecg', excerpt: 'AFib with rapid ventricular response' },
      { source: 'CheXpert+', modality: 'imaging', excerpt: 'Vascular congestion score 0.89' }
    )
  } else if (lowerInput.includes('differential') || lowerInput.includes('diagnosis')) {
    content = `**Differential Diagnosis** (Prioritized by Clinical Evidence)

1. **Acute Decompensated Heart Failure** (Primary) — 87%
   • BNP 1,240, CXR congestion, elevated JVP, edema
   • MIMIC-IV match: 2,847 cases, 78% ADHF

2. **Acute Coronary Syndrome / Demand Ischemia** — 23%
   • Troponin 0.45, AFib with RVR, known CAD
   • Type 2 MI likely given supply-demand mismatch

3. **Sepsis / Septic Cardiomyopathy** — 12%
   • Leukocytosis 14.2, lactate 2.8, fever 38.1°C
   • Blood cultures pending

4. **Pulmonary Embolism** — 8%
   • RV strain on ECG, elevated D-dimer 2.4
   • CTPA recommended if hemodynamically stable

5. **Hypertensive Emergency** — 5%
   • BP 182/98, end-organ dysfunction (AKI, encephalopathy)

**Recommended workup:** CTPA if Wells >4, repeat troponin q3h, lactate trend, blood cultures ×2, echo for RV function.`
  } else if (lowerInput.includes('risk') || lowerInput.includes('score')) {
    content = `**Calculated Risk Scores**

| Score | Value | Risk Category | Interpretation |
|-------|-------|---------------|----------------|
| **CHA₂DS₂-VASc** | 4 | High (4.8%/yr stroke) | Anticoagulation indicated (Apixaban ✓) |
| **HAS-BLED** | 3 | Moderate bleed risk | Caution with triple therapy |
| **GRACE 2.0** | 148 | High (8% in-hospital death) | Early invasive strategy if ACS |
| **CURB-65** | 2 | Moderate (9.2% 30-day) | Consider ICU if >2 |
| **SOFA** | 7 | High mortality risk | Multi-organ dysfunction |
| **MAGGIC** | 33 | 1-yr mortality 42% | Advanced HF referral |
| **Seattle HF** | — | 1-yr survival 68% | GDMT optimization critical |

**Action items:** Continue anticoagulation, optimize diuresis, nephrology consult for AKI, cardiology for GDMT uptitration once K+ normalized.`
  } else if (lowerInput.includes('guideline') || lowerInput.includes('guideline')) {
    content = `**Guideline Recommendations** (ESC 2021 HF / ACC 2023 / KDIGO 2024)

**Heart Failure (HFrEF, LVEF ≤40%) — ESC 2021 Class I:**
✅ ARNI (Sacubitril/valsartan) — *Held due to hyperkalemia*
✅ Beta-blocker (Carvedilol/Bisoprolol) — *Not started*
✅ MRA (Spironolactone/Eplerenone) — *Contraindicated K+ >5.0*
✅ SGLT2i (Empagliflozin/Dapagliflozin) — *Can initiate, renal-safe*

**Atrial Fibrillation — ACC/AHA 2023:**
✅ Anticoagulation (DOAC preferred) — Apixaban 5mg BID ✓
🔄 Rate control (Beta-blocker) — Not yet initiated
⚡ Rhythm control — Consider if symptomatic after rate control

**Hyperkalemia — KDIGO 2024:**
• K+ 6.2 = Severe — IV Calcium gluconate, Insulin/Dextrose, Albuterol, K+ binders
• Review RAASi — Lisinopril held appropriately

**Acute Kidney Injury — KDIGO 2024:**
• Stage 2 (Cr 2.8, baseline est. 1.1) — Nephrology consult, avoid nephrotoxins, optimize volume`
  } else if (lowerInput.includes('drug') || lowerInput.includes('interaction') || lowerInput.includes('medication')) {
    content = `**Medication Review — Interactions & Dosing**

| Drug | Dose | Interaction Risk | Renal Adjustment | Action |
|------|------|------------------|------------------|--------|
| **Furosemide** | 40mg IV q12h | Loop + ACEi = AKI risk ↑ | CrCl <30: ↑ dose | Continue, monitor K+/Cr |
| **Lisinopril** | 10mg daily | K+ ↑↑ with MRA/SGLT2i | CrCl <30: ↓ dose | **HELD** (K+ 6.2) |
| **Apixaban** | 5mg BID | ↑ bleed with antiplatelets | CrCl <25: 2.5mg BID | Continue, CrCl ~25 |
| **Insulin glargine** | 24u daily | K+ shift with β-agonist | No adjustment | Continue |
| **Spironolactone** | — | Contraindicated K+ >5.0 | CrCl <30: avoid | **DO NOT START** |
| **Empagliflozin** | — | Euglycemic DKA risk | CrCl ≥20: OK | **START** (renal-safe) |

**Key Interactions:**
⚠️ **Furosemide + Lisinopril** — Synergistic AKI risk (OR 2.3 in MIMIC)
⚠️ **Apixaban + Antiplatelet** — Major bleed HR 1.8 if combined
✅ **Empagliflozin + Loop** — Safe, reduces HF hospitalization 30%

**Recommendation:** Hold ACEi, start SGLT2i, initiate beta-blocker once euvolemic, avoid MRA until K+ <5.0.`
  } else if (lowerInput.includes('imaging') || lowerInput.includes('cxr') || lowerInput.includes('correlate')) {
    content = `**Imaging Correlation — Portable CXR (4h ago)**

**Findings:**
• Cardiomegaly (CTR 0.58) — chronic
• Pulmonary venous congestion (Kerley B lines) — acute
• Interstitial edema — acute
• No pleural effusion
• No pneumothorax

**AI Analysis (CheXpert+ / MedFusion):**
• **Pulmonary edema probability: 94%**
• **Cardiomegaly probability: 87%**
• **Pleural effusion probability: 12%**
• **Consolidation probability: 8%**

**Clinical Correlation:**
✅ BNP 1,240 — correlates with vascular congestion
✅ Crackles on exam — correlates with interstitial edema
✅ Orthopnea — correlates with cardiomegaly
❌ No fever/infiltrate — argues against pneumonia

**Recommendation:** Findings consistent with acute decompensated HF. No acute process requiring intervention beyond diuresis. Repeat CXR post-diuresis (24-48h). If no improvement, consider CTPA for occult PE.`
  } else {
    content = `I understand you're asking about: "${input}"

As MedFusion AI, I can provide clinical decision support for:
• Patient summarization & timeline synthesis
• Differential diagnosis with evidence citations
• Risk score calculations (CHA₂DS₂-VASc, GRACE, SOFA, etc.)
• Guideline recommendations (ESC, ACC, KDIGO, Surviving Sepsis)
• Medication review (interactions, renal dosing, duplicates)
• Imaging-lab-clinical correlation

**Try one of these prompts:**
• "Summarize this patient's clinical picture"
• "Generate a differential diagnosis for the primary complaint"
• "Calculate relevant risk scores for this patient"
• "Check guideline recommendations for heart failure"
• "Review medications for interactions and dosing"
• "Correlate imaging findings with clinical data"

Or ask any clinical question — I'll provide evidence-based reasoning with MIMIC-IV/PTB-XL/CheXpert+ citations.`
  }

  return { role: 'assistant', content, timestamp: new Date(), citations }
}