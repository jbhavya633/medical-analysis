// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi, beforeAll } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { QmlBenchmark } from '../../services/api'
import { QuantumLab } from '../QuantumLab'

const metric = (mean: number) => ({ mean, std: 0.01 })
const model = (family: 'classical' | 'quantum' | 'hybrid', acc: number) => ({
  family,
  metrics: {
    accuracy: metric(acc), sensitivity: metric(0.9), specificity: metric(0.95), auc: metric(0.97), f1: metric(0.9),
    train_time_s: metric(0.5), infer_ms_per_sample: metric(0.1),
  },
  roc: { fpr: [0, 0.1, 1], tpr: [0, 0.8, 1] },
  learning_curve: [{ n_train: 40, train_accuracy: 0.95, val_accuracy: 0.9 }],
  n_qubits: family === 'classical' ? null : 6,
  circuit_depth: family === 'classical' ? null : 25,
  n_params: 10,
  holdout: { accuracy: acc },
  explain: { selected_features: ['f1', 'f2'], permutation_importance: { f1: 0.1, f2: 0.02 }, shap_mean_abs: null },
})

const BENCHMARK: QmlBenchmark = {
  generated_at: '2026-10-08T00:00:00+00:00',
  git_commit: 'abc1234',
  runtime_s: 1,
  disclaimer: 'Not a diagnostic tool.',
  config: {},
  trained_models: [],
  datasets: {
    breast_cancer: {
      info: { title: 'Breast Cancer Wisconsin (Diagnostic)', positive_class: 'malignant', source: 'UCI', licence: 'CC BY 4.0', url: '' },
      n_samples: 569,
      positive_rate: 0.37,
      models: { logreg: model('classical', 0.9512), qsvm: model('quantum', 0.8861) },
    },
  },
}

vi.mock('../../services/api', () => ({
  qmlApi: {
    getBenchmark: vi.fn(() => Promise.resolve(BENCHMARK)),
    train: vi.fn(),
    getJob: vi.fn(),
    getModel: vi.fn(),
    predict: vi.fn(),
  },
}))

beforeAll(() => {
  globalThis.ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  } as unknown as typeof ResizeObserver
})

afterEach(cleanup)

async function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(<QueryClientProvider client={client}><QuantumLab /></QueryClientProvider>)
}

describe('QuantumLab', () => {
  it('always shows the not-a-diagnostic-tool disclaimer', async () => {
    await renderPage()
    expect(screen.getByRole('alert').textContent).toMatch(/not a diagnostic tool/i)
  }, 30000)

  it('renders the comparison table from the API response', async () => {
    await renderPage()
    expect(await screen.findByText(/Classical vs quantum: Breast Cancer Wisconsin/)).toBeTruthy()
    expect(screen.getAllByText('Quantum-kernel SVM').length).toBeGreaterThan(0)
    expect(screen.getByText('0.951')).toBeTruthy()
    expect(screen.getByText('0.886')).toBeTruthy()
  }, 30000)
})
