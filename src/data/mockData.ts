import { Patient, LabResult, VitalSigns } from '../types'

const now = new Date()
const hoursAgo = (h: number) => new Date(now.getTime() - h * 3600000).toISOString()
const daysAgo = (d: number) => new Date(now.getTime() - d * 86400000).toISOString()
const yearsAgo = (y: number) => new Date(now.getFullYear() - y, now.getMonth(), now.getDate()).toISOString()

function makeLabs(patientId: string): LabResult[] {
  const tests = [
    { name: 'Hemoglobin', cat: 'Hematology', val: 8.2, unit: 'g/dL', low: 12, high: 16, interp: 'low' as const, loinc: '718-7' },
    { name: 'WBC', cat: 'Hematology', val: 14.8, unit: 'K/uL', low: 4.5, high: 11, interp: 'high' as const, loinc: '6690-2' },
    { name: 'Platelets', cat: 'Hematology', val: 92, unit: 'K/uL', low: 150, high: 400, interp: 'low' as const, loinc: '777-3' },
    { name: 'Sodium', cat: 'Chemistry', val: 132, unit: 'mmol/L', low: 136, high: 145, interp: 'low' as const, loinc: '2951-2' },
    { name: 'Potassium', cat: 'Chemistry', val: 6.2, unit: 'mmol/L', low: 3.5, high: 5.1, interp: 'critical' as const, loinc: '2823-3' },
    { name: 'Creatinine', cat: 'Chemistry', val: 2.4, unit: 'mg/dL', low: 0.6, high: 1.2, interp: 'high' as const, loinc: '2160-0' },
    { name: 'BUN', cat: 'Chemistry', val: 48, unit: 'mg/dL', low: 7, high: 20, interp: 'high' as const, loinc: '3094-0' },
    { name: 'Glucose', cat: 'Chemistry', val: 186, unit: 'mg/dL', low: 70, high: 100, interp: 'high' as const, loinc: '2345-7' },
    { name: 'Troponin I', cat: 'Cardiac', val: 0.84, unit: 'ng/mL', low: 0, high: 0.04, interp: 'critical' as const, loinc: '10839-9' },
    { name: 'BNP', cat: 'Cardiac', val: 842, unit: 'pg/mL', low: 0, high: 100, interp: 'high' as const, loinc: '30934-4' },
    { name: 'Lactate', cat: 'Chemistry', val: 3.1, unit: 'mmol/L', low: 0.5, high: 2.2, interp: 'high' as const, loinc: '2524-7' },
    { name: 'INR', cat: 'Coagulation', val: 1.8, unit: '', low: 0.8, high: 1.2, interp: 'high' as const, loinc: '6301-6' },
    { name: 'ALT', cat: 'Liver', val: 62, unit: 'U/L', low: 7, high: 56, interp: 'high' as const, loinc: '1742-6' },
    { name: 'AST', cat: 'Liver', val: 78, unit: 'U/L', low: 10, high: 40, interp: 'high' as const, loinc: '1920-8' },
    { name: 'Albumin', cat: 'Liver', val: 2.8, unit: 'g/dL', low: 3.5, high: 5.0, interp: 'low' as const, loinc: '1751-7' },
    { name: 'HbA1c', cat: 'Endocrine', val: 8.4, unit: '%', low: 4.0, high: 5.6, interp: 'high' as const, loinc: '4548-4' },
    { name: 'TSH', cat: 'Endocrine', val: 2.1, unit: 'mIU/L', low: 0.4, high: 4.0, interp: 'normal' as const, loinc: '3016-3' },
    { name: 'CRP', cat: 'Inflammation', val: 48, unit: 'mg/L', low: 0, high: 5, interp: 'high' as const, loinc: '1988-5' },
  ]
  return tests.map((t, i) => ({
    id: `lab-${patientId}-${i}`,
    testId: t.loinc,
    testName: t.name,
    category: t.cat,
    value: t.val,
    unit: t.unit,
    referenceRange: { low: t.low, high: t.high, unit: t.unit },
    interpretation: t.interp,
    status: 'final' as const,
    orderedBy: 'Dr. Sarah Chen',
    performedBy: 'MIMIC Core Lab',
    orderedAt: hoursAgo(8 + i),
    collectedAt: hoursAgo(7 + i),
    resultedAt: hoursAgo(4 + i),
    loincCode: t.loinc,
  }))
}

function makeVitals(patientId: string): VitalSigns[] {
  return Array.from({ length: 24 }, (_, i) => {
    const t = hoursAgo(23 - i)
    return {
      id: `vit-${patientId}-${i}`,
      timestamp: t,
      temperature: 37.1 + Math.sin(i / 4) * 0.6 + (i > 18 ? 0.8 : 0),
      heartRate: 88 + Math.round(Math.sin(i / 3) * 12) + (i > 20 ? 18 : 0),
      respiratoryRate: 18 + Math.round(Math.sin(i / 5) * 3),
      bloodPressureSystolic: 142 + Math.round(Math.sin(i / 4) * 10),
      bloodPressureDiastolic: 88 + Math.round(Math.cos(i / 4) * 6),
      oxygenSaturation: 94 - (i > 16 ? 2 : 0) + Math.round(Math.sin(i) * 1),
      weight: 82.4,
      height: 168,
      bmi: 29.2,
      painScore: i > 18 ? 6 : 3,
      source: 'device' as const,
    }
  })
}

const PROVIDER = {
  id: 'prov-1',
  name: 'Dr. Sarah Chen',
  npi: '1234567890',
  specialty: 'Internal Medicine / Critical Care',
  organization: 'Beth Israel Deaconess Medical Center',
  phone: '+1-617-555-0100',
  email: 'schen@bidmc.harvard.edu',
}

export const MOCK_PATIENTS: Patient[] = [
  {
    id: '10012853',
    mrn: 'MIMIC-10012853',
    firstName: 'Elena',
    lastName: 'Vasquez',
    dateOfBirth: yearsAgo(67),
    sex: 'F',
    phone: '+1-617-555-0142',
    email: 'e.vasquez@example.com',
    address: { street: '14 Beacon St', city: 'Boston', state: 'MA', zipCode: '02108', country: 'US' },
    insurance: { provider: 'Medicare', policyNumber: '1EG4-TE5-MK72', subscriberId: '10012853', relationship: 'self', effectiveDate: daysAgo(400) },
    emergencyContact: { name: 'Miguel Vasquez', relationship: 'Spouse', phone: '+1-617-555-0143' },
    primaryCareProvider: PROVIDER,
    allergies: [
      { id: 'a1', substance: 'Penicillin', reaction: ['Rash', 'Anaphylaxis'], severity: 'life-threatening', status: 'active', notedDate: daysAgo(2000) },
      { id: 'a2', substance: 'Iodine contrast', reaction: ['Urticaria'], severity: 'moderate', status: 'active', notedDate: daysAgo(400) },
    ],
    medications: [
      { id: 'm1', name: 'Furosemide', genericName: 'Furosemide', dosage: '40 mg', route: 'PO', frequency: 'BID', startDate: daysAgo(30), status: 'active', prescribingProvider: 'Dr. Sarah Chen', indication: 'CHF' },
      { id: 'm2', name: 'Lisinopril', genericName: 'Lisinopril', dosage: '10 mg', route: 'PO', frequency: 'Daily', startDate: daysAgo(180), status: 'active', prescribingProvider: 'Dr. Sarah Chen', indication: 'HTN / HFrEF' },
      { id: 'm3', name: 'Metformin', genericName: 'Metformin', dosage: '1000 mg', route: 'PO', frequency: 'BID', startDate: daysAgo(900), status: 'held', prescribingProvider: 'Dr. Sarah Chen', indication: 'T2DM — held for AKI' },
      { id: 'm4', name: 'Aspirin', genericName: 'Aspirin', dosage: '81 mg', route: 'PO', frequency: 'Daily', startDate: daysAgo(400), status: 'active', prescribingProvider: 'Dr. Sarah Chen', indication: 'CAD' },
      { id: 'm5', name: 'Atorvastatin', genericName: 'Atorvastatin', dosage: '40 mg', route: 'PO', frequency: 'Nightly', startDate: daysAgo(400), status: 'active', prescribingProvider: 'Dr. Sarah Chen', indication: 'Hyperlipidemia' },
      { id: 'm6', name: 'Insulin glargine', genericName: 'Insulin glargine', dosage: '18 units', route: 'SC', frequency: 'Nightly', startDate: daysAgo(2), status: 'active', prescribingProvider: 'Dr. Sarah Chen', indication: 'Hyperglycemia' },
    ],
    conditions: [
      { id: 'c1', code: 'I50.22', display: 'Chronic systolic heart failure', category: 'diagnosis', severity: 'severe', status: 'active', onsetDate: daysAgo(800), clinicalStatus: 'active', verificationStatus: 'confirmed' },
      { id: 'c2', code: 'E11.22', display: 'Type 2 diabetes mellitus with diabetic CKD', category: 'diagnosis', severity: 'moderate', status: 'active', onsetDate: daysAgo(2200), clinicalStatus: 'active', verificationStatus: 'confirmed' },
      { id: 'c3', code: 'N18.3', display: 'Chronic kidney disease, stage 3', category: 'diagnosis', severity: 'moderate', status: 'active', onsetDate: daysAgo(600), clinicalStatus: 'active', verificationStatus: 'confirmed' },
      { id: 'c4', code: 'I25.10', display: 'Atherosclerotic heart disease of native coronary artery', category: 'diagnosis', status: 'active', onsetDate: daysAgo(400), clinicalStatus: 'active', verificationStatus: 'confirmed' },
      { id: 'c5', code: 'I48.91', display: 'Unspecified atrial fibrillation', category: 'diagnosis', status: 'active', onsetDate: daysAgo(1), clinicalStatus: 'active', verificationStatus: 'provisional' },
    ],
    encounters: [
      {
        id: 'enc-1',
        type: 'emergency',
        status: 'in-progress',
        class: 'EMER',
        priority: 'urgent',
        subject: '10012853',
        participant: [{ individual: PROVIDER, type: ['attending'], period: { start: hoursAgo(14) } }],
        period: { start: hoursAgo(14) },
        location: [{ location: { id: 'ed-12', name: 'ED Bay 12', type: 'ED' }, status: 'active', period: { start: hoursAgo(14) } }],
        serviceProvider: 'BIDMC Emergency',
        diagnosis: [],
        reasonCode: [{ coding: [{ system: 'ICD-10', code: 'R06.02', display: 'Shortness of breath' }], text: 'Dyspnea, chest pressure' }],
      },
    ],
    vitals: makeVitals('10012853'),
    labResults: makeLabs('10012853'),
    imagingStudies: [
      {
        id: 'img-1',
        accessionNumber: 'ACC-CXR-5123',
        studyInstanceUID: '1.2.840.113619.2.55.3.604688.5123',
        studyDate: daysAgo(0).slice(0, 10),
        studyTime: '08:42:00',
        modality: 'XRAY',
        bodyPart: 'CHEST',
        description: 'Chest X-ray PA and Lateral — MIMIC-CXR style',
        status: 'completed',
        referringPhysician: 'Dr. Sarah Chen',
        performingPhysician: 'Dr. James Park, Radiology',
        institution: 'BIDMC',
        stationName: 'CR-ED-01',
        series: [{
          id: 'ser-1',
          seriesInstanceUID: '1.2.840.113619.2.55.3.604688.5123.1',
          seriesNumber: 1,
          seriesDate: daysAgo(0).slice(0, 10),
          seriesTime: '08:42:00',
          modality: 'XRAY',
          description: 'PA Chest',
          bodyPart: 'CHEST',
          instanceCount: 2,
          instances: [],
        }],
        aiFindings: [
          { id: 'f1', modelId: 'chexpert-plus-v2', modelVersion: '2.1.0', finding: 'Cardiomegaly', confidence: 0.91, category: 'cardiomegaly', severity: 'moderate', status: 'pending', createdAt: hoursAgo(5) },
          { id: 'f2', modelId: 'chexpert-plus-v2', modelVersion: '2.1.0', finding: 'Pulmonary edema / congestion', confidence: 0.84, category: 'edema', severity: 'moderate', status: 'pending', createdAt: hoursAgo(5) },
          { id: 'f3', modelId: 'chexpert-plus-v2', modelVersion: '2.1.0', finding: 'Possible small pleural effusion (R)', confidence: 0.62, category: 'effusion', severity: 'low', status: 'pending', createdAt: hoursAgo(5) },
        ],
        report: {
          id: 'rpt-1',
          reportStatus: 'preliminary',
          reportText: 'PA and lateral chest radiograph. Heart size is enlarged. There is interstitial prominence consistent with pulmonary venous congestion. Small right pleural effusion. No pneumothorax. Osseous structures intact.',
          codedDiagnosis: [{ coding: [{ system: 'ICD-10', code: 'I50.1', display: 'Left ventricular failure' }] }],
          conclusion: 'Cardiomegaly with pulmonary edema, small R effusion.',
          signedBy: 'Dr. James Park',
          signedAt: hoursAgo(4),
        },
      },
      {
        id: 'img-2',
        accessionNumber: 'ACC-CT-8891',
        studyInstanceUID: '1.2.840.113619.2.55.3.604688.8891',
        studyDate: daysAgo(1).slice(0, 10),
        studyTime: '14:10:00',
        modality: 'CT',
        bodyPart: 'CHEST',
        description: 'CT Chest with contrast — PE protocol',
        status: 'completed',
        referringPhysician: 'Dr. Sarah Chen',
        performingPhysician: 'Dr. Amina Rahman, Radiology',
        institution: 'BIDMC',
        stationName: 'CT-03',
        series: [{
          id: 'ser-2',
          seriesInstanceUID: '1.2.840.113619.2.55.3.604688.8891.1',
          seriesNumber: 1,
          seriesDate: daysAgo(1).slice(0, 10),
          seriesTime: '14:10:00',
          modality: 'CT',
          description: 'Axial 1.25 mm',
          bodyPart: 'CHEST',
          instanceCount: 248,
          instances: [],
        }],
        aiFindings: [
          { id: 'f4', modelId: 'ct-pe-detector', modelVersion: '1.4.0', finding: 'No filling defect in main/lobar PAs', confidence: 0.88, category: 'other', severity: 'low', status: 'confirmed', reviewedBy: 'Dr. Amina Rahman', reviewedAt: hoursAgo(20), createdAt: hoursAgo(22) },
        ],
      },
    ],
    ecgStudies: [
      {
        id: 'ecg-1',
        accessionNumber: 'ECG-PTBXL-00456',
        studyDate: daysAgo(0).slice(0, 10),
        studyTime: '07:18:00',
        deviceId: 'GE-MAC5500',
        deviceModel: 'GE MAC 5500 HD',
        leads: [],
        interpretation: {
          rhythm: 'Atrial fibrillation',
          rate: 118,
          axis: -30,
          intervals: { pr: undefined, qrs: 92, qt: 340, qtc: 478, rr: 508 },
          findings: ['Atrial fibrillation with RVR', 'Nonspecific ST-T changes', 'Possible LVH'],
          conclusion: 'AF with rapid ventricular response. QTc prolonged.',
          cardiologist: 'Dr. Priya Nair',
          verifiedAt: hoursAgo(6),
        },
        aiAnalysis: {
          modelId: 'ptbxl-ecg-transformer',
          modelVersion: '1.0.3',
          abnormalities: [
            { type: 'AFIB', description: 'Atrial fibrillation', confidence: 0.94, leadLocations: ['II', 'V1'] },
            { type: 'STTC', description: 'ST-T changes', confidence: 0.71, leadLocations: ['V4', 'V5', 'V6'] },
            { type: 'LVH', description: 'Left ventricular hypertrophy', confidence: 0.58, leadLocations: ['V5', 'V6'] },
          ],
          overallConfidence: 0.89,
          processingTime: 0.42,
        },
        sampledAt: hoursAgo(7),
        duration: 10,
        samplingRate: 500,
        filterSettings: { lowPass: 40, highPass: 0.5, notchFilter: 60, muscleFilter: true },
        // Additional fields for ECGAnalyzer
        rhythm: 'afib',
        heartRate: 118,
        prInterval: 0,
        qrsDuration: 92,
        qtInterval: 340,
        qtcInterval: 478,
        pAxis: 0,
        qrsAxis: -30,
        tAxis: 0,
        acquiredAt: hoursAgo(7),
      },
    ],
    clinicalNotes: [
      {
        id: 'n1',
        type: 'admission',
        title: 'ED H&P — MIMIC-IV-Note style',
        content: '67F with HFrEF (EF 30%), T2DM, CKD3 presenting with 3 days of progressive dyspnea, orthopnea, and chest pressure. On arrival tachypneic, SpO2 91% on RA, irregularly irregular tachycardic. Labs notable for K 6.2, Cr 2.4 (baseline 1.4), troponin 0.84, BNP 842. CXR with pulmonary edema. ECG AF with RVR. Started on BiPAP, IV furosemide, insulin/glucose for hyperK. Held metformin. Plan: admit CCU, rate control, ischemia workup, nephrology for AKI on CKD.',
        author: PROVIDER,
        authoredAt: hoursAgo(12),
        status: 'signed',
        encounterId: 'enc-1',
        tags: ['CHF', 'AF', 'AKI', 'hyperkalemia'],
        aiSummary: 'Decompensated HFrEF with new AF-RVR, AKI, hyperkalemia, and possible ACS.',
        aiKeyPoints: ['New AF with RVR', 'Hyperkalemia 6.2', 'AKI on CKD (Cr 2.4 from 1.4)', 'Elevated troponin — possible type 2 vs NSTEMI', 'Pulmonary edema on CXR'],
      },
    ],
    riskScores: [
      { id: 'rs1', name: 'MELD-Na', score: 18, maxScore: 40, category: 'moderate', factors: [{ name: 'Creatinine', value: 2.4, weight: 0.4, contribution: 7 }, { name: 'Bilirubin', value: 1.1, weight: 0.2, contribution: 2 }, { name: 'INR', value: 1.8, weight: 0.3, contribution: 6 }, { name: 'Sodium', value: 132, weight: 0.1, contribution: 3 }], calculatedAt: hoursAgo(3), reference: 'UNOS MELD-Na' },
      { id: 'rs2', name: 'HEART Score', score: 6, maxScore: 10, category: 'high', factors: [{ name: 'History', value: 'moderately suspicious', weight: 1, contribution: 1 }, { name: 'ECG', value: 'significant ST deviation', weight: 2, contribution: 2 }, { name: 'Age', value: 67, weight: 2, contribution: 2 }, { name: 'Risk factors', value: 4, weight: 2, contribution: 2 }, { name: 'Troponin', value: '2x ULN', weight: 2, contribution: 2 }], calculatedAt: hoursAgo(6), reference: 'Six et al. HEART score' },
      { id: 'rs3', name: 'CHA2DS2-VASc', score: 5, maxScore: 9, category: 'high', factors: [{ name: 'CHF', value: 1, weight: 1, contribution: 1 }, { name: 'Hypertension', value: 1, weight: 1, contribution: 1 }, { name: 'Age ≥75', value: 0, weight: 2, contribution: 0 }, { name: 'Diabetes', value: 1, weight: 1, contribution: 1 }, { name: 'Stroke/TIA', value: 0, weight: 2, contribution: 0 }, { name: 'Vascular disease', value: 1, weight: 1, contribution: 1 }, { name: 'Age 65-74', value: 1, weight: 1, contribution: 1 }, { name: 'Sex (female)', value: 1, weight: 1, contribution: 1 }], calculatedAt: hoursAgo(6), reference: 'ESC AF guidelines' },
    ],
    aiInsights: [
      {
        id: 'ai1', type: 'diagnosis', title: 'Likely acute decompensated HFrEF + AF-RVR',
        description: 'Multimodal fusion of CXR edema, BNP 842, AF on ECG, and rising Cr supports ADHF. Troponin elevation may be type 2 MI vs NSTEMI — serial trop and cardiology review recommended.',
        confidence: 0.87, evidence: [
          { type: 'lab', reference: 'BNP 842, Troponin 0.84', description: 'Cardiac biomarkers elevated', strength: 'strong' },
          { type: 'imaging', reference: 'CXR ACC-5123', description: 'Cardiomegaly + pulmonary edema', strength: 'strong' },
          { type: 'vital', reference: 'HR 118 irregular, SpO2 91%', description: 'Hemodynamic stress', strength: 'moderate' },
        ],
        actionable: true, actions: [{ label: 'Order serial troponin', type: 'order', payload: { test: 'troponin' } }, { label: 'Cardiology consult', type: 'referral', payload: { service: 'cardiology' } }],
        priority: 'critical', status: 'new', createdAt: hoursAgo(4), modelId: 'medfusion-multimodal', modelVersion: '0.9.0',
        recommendations: ['Order serial troponin I q6h x 3', 'Cardiology consultation for possible NSTEMI', 'Diuresis with IV furosemide', 'Rate control for AF-RVR'],
      },
      {
        id: 'ai2', type: 'treatment', title: 'Hyperkalemia protocol indicated',
        description: 'K+ 6.2 with AKI. ECG does not show peaked T waves yet. Insulin/glucose already given. Recheck K in 2h. Avoid ACE-I intensification until K and Cr stabilize. Calcium if ECG changes.',
        confidence: 0.93, evidence: [{ type: 'lab', reference: 'K 6.2, Cr 2.4', description: 'Severe hyperK with AKI', strength: 'strong' }],
        actionable: true, actions: [{ label: 'Repeat BMP in 2 hours', type: 'order', payload: { test: 'bmp' } }],
        priority: 'high', status: 'new', createdAt: hoursAgo(4), modelId: 'medfusion-cds', modelVersion: '0.9.0',
        recommendations: ['Repeat BMP in 2 hours', 'Monitor ECG for peaked T waves', 'Hold ACE inhibitors/ARBs', 'Consider calcium gluconate if ECG changes'],
      },
      {
        id: 'ai3', type: 'interaction', title: 'Metformin held — lactic acidosis risk',
        description: 'Metformin + AKI (Cr 2.4) + lactate 3.1. Appropriately held. Do not restart until eGFR > 45 and lactate normalizes.',
        confidence: 0.96, evidence: [{ type: 'medication', reference: 'Metformin', description: 'Contraindicated in AKI', strength: 'strong' }, { type: 'lab', reference: 'Lactate 3.1', description: 'Elevated lactate', strength: 'moderate' }],
        actionable: false, priority: 'medium', status: 'acknowledged', createdAt: hoursAgo(5), acknowledgedAt: hoursAgo(4), acknowledgedBy: 'Dr. Sarah Chen', modelId: 'medfusion-cds', modelVersion: '0.9.0',
        recommendations: ['Continue metformin hold', 'Monitor lactate q6h', 'Restart metformin only when eGFR > 45 and lactate normal'],
      },
    ],
    createdAt: daysAgo(1200),
    updatedAt: hoursAgo(1),
  },
  {
    id: '10020740',
    mrn: 'MIMIC-10020740',
    firstName: 'James',
    lastName: 'Okafor',
    dateOfBirth: yearsAgo(54),
    sex: 'M',
    phone: '+1-617-555-0198',
    primaryCareProvider: PROVIDER,
    allergies: [],
    medications: [
      { id: 'm7', name: 'Albuterol', dosage: '2 puffs', route: 'INH', frequency: 'Q4H PRN', startDate: daysAgo(5), status: 'active', prescribingProvider: 'Dr. Sarah Chen', indication: 'Asthma/COPD' },
    ],
    conditions: [
      { id: 'c6', code: 'J44.1', display: 'COPD with acute exacerbation', category: 'diagnosis', severity: 'moderate', status: 'active', clinicalStatus: 'active', verificationStatus: 'confirmed' },
    ],
    encounters: [],
    vitals: makeVitals('10020740').map(v => ({ ...v, oxygenSaturation: 89 + Math.round(Math.random() * 4), respiratoryRate: 24 })),
    labResults: makeLabs('10020740').map(l => l.testName === 'Potassium' ? { ...l, value: 4.1, interpretation: 'normal' as const } : l),
    imagingStudies: [{
      id: 'img-3', accessionNumber: 'ACC-CXR-2201', studyInstanceUID: '1.2.840.113619.2.55.3.604688.2201',
      studyDate: daysAgo(0).slice(0, 10), studyTime: '11:00:00', modality: 'XRAY', bodyPart: 'CHEST',
      description: 'Portable chest X-ray', status: 'completed', referringPhysician: 'Dr. Sarah Chen',
      performingPhysician: 'Dr. James Park', institution: 'BIDMC', stationName: 'CR-PORT-02',
      series: [{ id: 'ser-3', seriesInstanceUID: 'x', seriesNumber: 1, seriesDate: daysAgo(0).slice(0, 10), seriesTime: '11:00:00', modality: 'XRAY', description: 'AP portable', bodyPart: 'CHEST', instanceCount: 1, instances: [] }],
      aiFindings: [{ id: 'f5', modelId: 'chexpert-plus-v2', modelVersion: '2.1.0', finding: 'Hyperinflation, no infiltrate', confidence: 0.77, category: 'other', severity: 'low', status: 'pending', createdAt: hoursAgo(2) }],
    }],
    ecgStudies: [],
    clinicalNotes: [],
    riskScores: [{ id: 'rs4', name: 'CURB-65', score: 1, maxScore: 5, category: 'low', factors: [{ name: 'Urea', value: 18, weight: 1, contribution: 0 }, { name: 'RR', value: 24, weight: 1, contribution: 0 }, { name: 'BP', value: '132/78', weight: 1, contribution: 0 }, { name: 'Age', value: 54, weight: 1, contribution: 0 }, { name: 'Confusion', value: 'no', weight: 1, contribution: 0 }], calculatedAt: hoursAgo(2), reference: 'BTS CURB-65' }],
    aiInsights: [{
      id: 'ai4', type: 'diagnosis', title: 'COPD exacerbation — low pneumonia probability',
      description: 'CXR without infiltrate, CURB-65 = 1. Supportive care + bronchodilators. Consider steroids.',
      confidence: 0.81, evidence: [{ type: 'imaging', reference: 'CXR 2201', description: 'No infiltrate', strength: 'moderate' }],
      actionable: true, actions: [{ label: 'Steroid burst', type: 'medication', payload: { drug: 'prednisone' } }],
      priority: 'medium', status: 'new', createdAt: hoursAgo(2), modelId: 'medfusion-multimodal', modelVersion: '0.9.0',
      recommendations: ['Prednisone 40mg PO daily x 5 days', 'Increase bronchodilator frequency', 'Follow-up CXR if no improvement in 48h'],
    }],
    createdAt: daysAgo(80),
    updatedAt: hoursAgo(2),
  },
  {
    id: '10021487',
    mrn: 'MIMIC-10021487',
    firstName: 'Mei',
    lastName: 'Chen',
    dateOfBirth: yearsAgo(78),
    sex: 'F',
    primaryCareProvider: PROVIDER,
    allergies: [{ id: 'a3', substance: 'Sulfa', reaction: ['Rash'], severity: 'mild', status: 'active', notedDate: daysAgo(3000) }],
    medications: [
      { id: 'm8', name: 'Donepezil', dosage: '10 mg', route: 'PO', frequency: 'Nightly', startDate: daysAgo(400), status: 'active', prescribingProvider: 'Dr. Sarah Chen', indication: 'Alzheimer disease' },
      { id: 'm9', name: 'Memantine', dosage: '10 mg', route: 'PO', frequency: 'BID', startDate: daysAgo(200), status: 'active', prescribingProvider: 'Dr. Sarah Chen', indication: 'Alzheimer disease' },
    ],
    conditions: [
      { id: 'c7', code: 'G30.9', display: 'Alzheimer disease, unspecified', category: 'diagnosis', severity: 'moderate', status: 'active', clinicalStatus: 'active', verificationStatus: 'confirmed' },
      { id: 'c8', code: 'I10', display: 'Essential hypertension', category: 'diagnosis', status: 'active', clinicalStatus: 'active', verificationStatus: 'confirmed' },
    ],
    encounters: [],
    vitals: makeVitals('10021487'),
    labResults: makeLabs('10021487').filter(l => ['Sodium', 'Potassium', 'Creatinine', 'Glucose', 'TSH'].includes(l.testName)).map(l => ({ ...l, interpretation: 'normal' as const, value: l.testName === 'Sodium' ? 140 : l.testName === 'Potassium' ? 4.2 : l.testName === 'Creatinine' ? 0.9 : l.testName === 'Glucose' ? 98 : 1.8 })),
    imagingStudies: [{
      id: 'img-4', accessionNumber: 'ACC-MR-3301', studyInstanceUID: '1.2.840.113619.2.55.3.604688.3301',
      studyDate: daysAgo(12).slice(0, 10), studyTime: '09:30:00', modality: 'MR', bodyPart: 'BRAIN',
      description: 'MRI Brain without contrast — ADNI-style protocol', status: 'completed',
      referringPhysician: 'Dr. Sarah Chen', performingPhysician: 'Dr. Lisa Cho, Neuroradiology',
      institution: 'BIDMC', stationName: 'MR-NEURO-01',
      series: [
        { id: 'ser-4a', seriesInstanceUID: 'a', seriesNumber: 1, seriesDate: daysAgo(12).slice(0, 10), seriesTime: '09:30:00', modality: 'MR', description: 'T1 MPRAGE', bodyPart: 'BRAIN', instanceCount: 176, instances: [] },
        { id: 'ser-4b', seriesInstanceUID: 'b', seriesNumber: 2, seriesDate: daysAgo(12).slice(0, 10), seriesTime: '09:40:00', modality: 'MR', description: 'T2 FLAIR', bodyPart: 'BRAIN', instanceCount: 32, instances: [] },
      ],
      aiFindings: [
        { id: 'f6', modelId: 'adni-brain-seg', modelVersion: '1.2.0', finding: 'Hippocampal atrophy (Scheltens 3)', confidence: 0.86, category: 'other', severity: 'moderate', status: 'confirmed', createdAt: daysAgo(11) },
        { id: 'f7', modelId: 'adni-brain-seg', modelVersion: '1.2.0', finding: 'Moderate small vessel ischemic change', confidence: 0.79, category: 'other', severity: 'low', status: 'confirmed', createdAt: daysAgo(11) },
      ],
    }],
    ecgStudies: [],
    clinicalNotes: [],
    riskScores: [],
    aiInsights: [{
      id: 'ai5', type: 'monitoring', title: 'Neurodegenerative trajectory — ADNI-aligned',
      description: 'MRI hippocampal atrophy consistent with AD continuum. Recommend MoCA, consider amyloid PET if disease-modifying therapy being considered.',
      confidence: 0.74, evidence: [{ type: 'imaging', reference: 'MRI 3301', description: 'Hippocampal atrophy', strength: 'strong' }],
      actionable: true, actions: [{ label: 'Order MoCA', type: 'order', payload: {} }],
      priority: 'low', status: 'new', createdAt: daysAgo(10), modelId: 'medfusion-neuro', modelVersion: '0.3.0',
      recommendations: ['Order MoCA', 'Consult Neurology', 'Discuss amyloid PET imaging'],
    }],
    createdAt: daysAgo(500),
    updatedAt: daysAgo(10),
  },
  {
    id: '10023117',
    mrn: 'MIMIC-10023117',
    firstName: 'Robert',
    lastName: 'Hale',
    dateOfBirth: yearsAgo(61),
    sex: 'M',
    primaryCareProvider: PROVIDER,
    allergies: [],
    medications: [
      { id: 'm10', name: 'Carboplatin', dosage: 'AUC 5', route: 'IV', frequency: 'q21d', startDate: daysAgo(40), status: 'active', prescribingProvider: 'Dr. Nina Patel', indication: 'NSCLC' },
    ],
    conditions: [
      { id: 'c9', code: 'C34.11', display: 'Malignant neoplasm of upper lobe, right bronchus or lung', category: 'diagnosis', severity: 'severe', status: 'active', clinicalStatus: 'active', verificationStatus: 'confirmed' },
    ],
    encounters: [],
    vitals: makeVitals('10023117'),
    labResults: makeLabs('10023117'),
    imagingStudies: [{
      id: 'img-5', accessionNumber: 'ACC-PETCT-4410', studyInstanceUID: '1.2.840.113619.2.55.3.604688.4410',
      studyDate: daysAgo(7).slice(0, 10), studyTime: '13:00:00', modality: 'PET', bodyPart: 'WHOLEBODY',
      description: 'FDG PET/CT — AutoPET-style whole body', status: 'completed',
      referringPhysician: 'Dr. Nina Patel', performingPhysician: 'Dr. Omar Said, Nuclear Medicine',
      institution: 'BIDMC', stationName: 'PETCT-01',
      series: [
        { id: 'ser-5a', seriesInstanceUID: 'p', seriesNumber: 1, seriesDate: daysAgo(7).slice(0, 10), seriesTime: '13:00:00', modality: 'PT', description: 'PET AC', bodyPart: 'WHOLEBODY', instanceCount: 287, instances: [] },
        { id: 'ser-5b', seriesInstanceUID: 'c', seriesNumber: 2, seriesDate: daysAgo(7).slice(0, 10), seriesTime: '13:00:00', modality: 'CT', description: 'CT AC / fusion', bodyPart: 'WHOLEBODY', instanceCount: 287, instances: [] },
      ],
      aiFindings: [
        { id: 'f8', modelId: 'autopet-seg', modelVersion: '2.0.0', finding: 'RUL FDG-avid mass SUVmax 12.4 (28 mL)', confidence: 0.92, category: 'mass', severity: 'high', status: 'confirmed', createdAt: daysAgo(6) },
        { id: 'f9', modelId: 'autopet-seg', modelVersion: '2.0.0', finding: 'Right hilar node SUVmax 6.1', confidence: 0.81, category: 'lesion', severity: 'moderate', status: 'pending', createdAt: daysAgo(6) },
      ],
    }],
    ecgStudies: [],
    clinicalNotes: [],
    riskScores: [],
    aiInsights: [{
      id: 'ai6', type: 'diagnosis', title: 'AutoPET segmentation: dominant RUL lesion + hilar node',
      description: 'Tumor volume 28 mL. Consider restaging after cycle 2. No distant FDG-avid disease detected by model (sensitivity limited below 8 mm).',
      confidence: 0.85, evidence: [{ type: 'imaging', reference: 'PET/CT 4410', description: 'Segmented tumor + node', strength: 'strong' }],
      actionable: true, priority: 'high', status: 'new', createdAt: daysAgo(6), modelId: 'autopet-seg', modelVersion: '2.0.0',
      recommendations: ['Restaging after cycle 2', 'Monitor for distant FDG-avid disease', 'Continue chemotherapy protocol'],
    }],
    createdAt: daysAgo(90),
    updatedAt: daysAgo(6),
  },
  {
    id: '10037928',
    mrn: 'MIMIC-10037928',
    firstName: 'Sofia',
    lastName: 'Martinez',
    dateOfBirth: yearsAgo(42),
    sex: 'F',
    primaryCareProvider: PROVIDER,
    allergies: [],
    medications: [],
    conditions: [
      { id: 'c10', code: 'I50.1', display: 'Left ventricular failure', category: 'diagnosis', severity: 'moderate', status: 'active', clinicalStatus: 'active', verificationStatus: 'provisional' },
    ],
    encounters: [],
    vitals: makeVitals('10037928'),
    labResults: makeLabs('10037928').filter(l => ['Troponin I', 'BNP', 'Creatinine', 'Potassium'].includes(l.testName)),
    imagingStudies: [{
      id: 'img-6', accessionNumber: 'ACC-US-5502', studyInstanceUID: '1.2.840.113619.2.55.3.604688.5502',
      studyDate: daysAgo(0).slice(0, 10), studyTime: '16:20:00', modality: 'US', bodyPart: 'HEART',
      description: 'Transthoracic echo — EchoNet-Dynamic A4C', status: 'completed',
      referringPhysician: 'Dr. Sarah Chen', performingPhysician: 'Dr. Priya Nair',
      institution: 'BIDMC', stationName: 'ECHO-02',
      series: [{ id: 'ser-6', seriesInstanceUID: 'e', seriesNumber: 1, seriesDate: daysAgo(0).slice(0, 10), seriesTime: '16:20:00', modality: 'US', description: 'A4C cine', bodyPart: 'HEART', instanceCount: 1, instances: [] }],
      aiFindings: [
        { id: 'f10', modelId: 'echonet-dynamic', modelVersion: '1.0.0', finding: 'LVEF 32% (AI) — reduced systolic function', confidence: 0.89, category: 'other', severity: 'high', status: 'pending', createdAt: hoursAgo(1) },
      ],
    }],
    ecgStudies: [{
      id: 'ecg-2', accessionNumber: 'ECG-PTBXL-01802', studyDate: daysAgo(0).slice(0, 10), studyTime: '16:05:00',
      deviceId: 'PHILIPS-PageWriter', deviceModel: 'Philips PageWriter TC70', leads: [],
      interpretation: { rhythm: 'Sinus tachycardia', rate: 108, intervals: { pr: 156, qrs: 88, qt: 320, qtc: 428, rr: 555 }, findings: ['Sinus tachycardia', 'Nonspecific T-wave flattening'], conclusion: 'Sinus tach, otherwise unremarkable.' },
      aiAnalysis: { modelId: 'ptbxl-ecg-transformer', modelVersion: '1.0.3', abnormalities: [{ type: 'STACH', description: 'Sinus tachycardia', confidence: 0.91, leadLocations: ['II'] }], overallConfidence: 0.91, processingTime: 0.31 },
      sampledAt: hoursAgo(2), duration: 10, samplingRate: 500, filterSettings: { lowPass: 40, highPass: 0.5, notchFilter: 60 },
      // Additional fields for ECGAnalyzer
      rhythm: 'sinus',
      heartRate: 108,
      prInterval: 156,
      qrsDuration: 88,
      qtInterval: 320,
      qtcInterval: 428,
      pAxis: 60,
      qrsAxis: 45,
      tAxis: 45,
      acquiredAt: hoursAgo(2),
    }],
    clinicalNotes: [],
    riskScores: [],
    aiInsights: [{
      id: 'ai7', type: 'diagnosis', title: 'EchoNet LVEF 32% — new HFrEF phenotype',
      description: 'Video model estimates EF 32% from A4C. Correlate with formal Simpson biplane. Start GDMT if confirmed and no contraindication.',
      confidence: 0.82, evidence: [{ type: 'imaging', reference: 'Echo 5502', description: 'AI LVEF 32%', strength: 'moderate' }],
      actionable: true, priority: 'high', status: 'new', createdAt: hoursAgo(1), modelId: 'echonet-dynamic', modelVersion: '1.0.0',
      recommendations: ['Confirm LVEF with formal Simpson biplane', 'Initiate GDMT if confirmed', 'Cardiology referral for HFrEF management'],
    }],
    createdAt: daysAgo(2),
    updatedAt: hoursAgo(1),
  },
]

export const DATASETS = [
  { id: 'mimic-iv-demo', name: 'MIMIC-IV Clinical Demo', modality: 'Clinical', access: 'Public demo', size: '15.5 MB', subjects: 100, url: 'https://physionet.org/content/mimic-iv-demo/2.2/', role: 'Core EHR: labs, diagnoses, meds, encounters', status: 'ready' },
  { id: 'mimic-iv-ed-demo', name: 'MIMIC-IV-ED Demo', modality: 'ED / Symptoms', access: 'Public demo', size: '~5 MB', subjects: 100, url: 'https://physionet.org/content/mimic-iv-ed-demo/2.2/', role: 'Chief complaints, triage, ED vitals', status: 'ready' },
  { id: 'mimic-iv-ecg-demo', name: 'MIMIC-IV-ECG Demo', modality: 'ECG', access: 'Public demo', size: '76 MB', subjects: '~100', url: 'https://physionet.org/content/mimic-iv-ecg-demo/0.1/', role: 'Diagnostic ECGs linked to MIMIC-IV', status: 'ready' },
  { id: 'ptb-xl', name: 'PTB-XL v1.0.3', modality: 'ECG', access: 'CC BY 4.0', size: '~1.7 GB', subjects: 18869, url: 'https://physionet.org/content/ptb-xl/1.0.3/', role: '12-lead ECG classification (71 statements)', status: 'download' },
  { id: 'mimic-iv', name: 'MIMIC-IV', modality: 'Clinical', access: 'Credentialed', size: '~7 GB+', subjects: 300000, url: 'https://physionet.org/content/mimiciv/', role: 'Full EHR — request after CITI + DUA', status: 'credentialed' },
  { id: 'mimic-iv-note', name: 'MIMIC-IV-Note', modality: 'Notes', access: 'Credentialed', size: '~1 GB', subjects: 300000, url: 'https://physionet.org/content/mimic-iv-note/', role: 'Discharge + radiology reports', status: 'credentialed' },
  { id: 'mimic-cxr', name: 'MIMIC-CXR', modality: 'X-ray', access: 'Credentialed', size: '~500 GB', subjects: 65000, url: 'https://physionet.org/content/mimic-cxr/', role: 'Chest radiographs + reports', status: 'credentialed' },
  { id: 'chexpert-plus', name: 'CheXpert Plus', modality: 'X-ray + Report', access: 'Stanford AIMI', size: 'large', subjects: 64725, url: 'https://aimi.stanford.edu/datasets/chexpert-plus', role: '223k image-report pairs, 14 labels', status: 'portal' },
  { id: 'autopet', name: 'AutoPET-II', modality: 'PET + CT', access: 'Public research', size: 'large', subjects: 900, url: 'https://autopet.org/autopetii.html', role: 'Aligned PET/CT + tumor segmentation', status: 'portal' },
  { id: 'echonet', name: 'EchoNet-Dynamic', modality: 'Ultrasound', access: 'Registration', size: '~8 GB', subjects: 10030, url: 'https://echonet.github.io/dynamic/', role: 'Echo video → LVEF / cardiac motion', status: 'portal' },
  { id: 'adni', name: 'ADNI', modality: 'MRI + PET + Clinical', access: 'Research application', size: 'very large', subjects: 2000, url: 'https://adni.loni.usc.edu/', role: 'Neuroimaging + biomarkers', status: 'application' },
  { id: 'isic', name: 'ISIC Archive', modality: 'Dermatology', access: 'CC0 / CC-BY', size: 'varies', subjects: 100000, url: 'https://challenge.isic-archive.com/data/', role: 'Skin lesion classification / segmentation', status: 'download' },
  { id: 'ukb', name: 'UK Biobank', modality: 'Multimodal', access: 'Application', size: 'petabytes', subjects: 500000, url: 'https://www.ukbiobank.ac.uk/enable-your-research/apply-for-access/', role: 'Longitudinal imaging + health — do not start here', status: 'application' },
]

export const MODELS = [
  { id: 'ptbxl-ecg-transformer', name: 'PTB-XL ECG Transformer', version: '1.2.0', type: 'classification', modality: ['ECG'], task: '12-lead ECG multi-label', architecture: 'Transformer', framework: 'PyTorch', inputShape: [12, 5000], outputShape: [71], metrics: { auc: 0.931, f1: 0.812 }, trainingData: ['PTB-XL'], validationData: ['PTB-XL'], testData: ['PTB-XL'], artifacts: [], createdAt: '2024-01-15', updatedAt: '2024-06-20', status: 'deployed' },
  { id: 'chexpert-plus-v2', name: 'CheXpert Plus Vision-Language', version: '2.1.0', type: 'detection', modality: ['XRAY'], task: 'CXR 14-pathology + report', architecture: 'ResNet-50 + BERT', framework: 'PyTorch', inputShape: [3, 224, 224], outputShape: [14], metrics: { auc: 0.889, f1: 0.741 }, trainingData: ['CheXpert Plus'], validationData: ['CheXpert Plus'], testData: ['CheXpert Plus'], artifacts: [], createdAt: '2024-02-10', updatedAt: '2024-07-15', status: 'deployed' },
  { id: 'autopet-seg', name: 'AutoPET nnU-Net', version: '1.0.0', type: 'segmentation', modality: ['PET', 'CT'], task: 'PET/CT tumor segmentation', architecture: 'nnU-Net', framework: 'PyTorch', inputShape: [2, 128, 128, 128], outputShape: [1, 128, 128, 128], metrics: { dice: 0.78, iou: 0.66 }, trainingData: ['AutoPET-II'], validationData: ['AutoPET-II'], testData: ['AutoPET-II'], artifacts: [], createdAt: '2024-03-01', updatedAt: '2024-08-01', status: 'deployed' },
  { id: 'echonet-dynamic', name: 'EchoNet-Dynamic', version: '1.3.0', type: 'regression', modality: ['US'], task: 'Echo LVEF regression', architecture: 'R(2+1)D', framework: 'PyTorch', inputShape: [3, 16, 112, 112], outputShape: [1], metrics: { mae: 4.1 }, trainingData: ['EchoNet-Dynamic'], validationData: ['EchoNet-Dynamic'], testData: ['EchoNet-Dynamic'], artifacts: [], createdAt: '2024-01-20', updatedAt: '2024-05-30', status: 'deployed' },
  { id: 'medfusion-multimodal', name: 'MedFusion Evidence Fusion', version: '0.9.0', type: 'multimodal', modality: ['ECG', 'XRAY', 'Clinical'], task: 'Cross-modal clinical assessment', architecture: 'Fusion Transformer', framework: 'PyTorch', inputShape: [1000], outputShape: [50], metrics: { auc: 0.84 }, trainingData: ['MIMIC-IV', 'MIMIC-CXR', 'MIMIC-IV-ECG'], validationData: ['MIMIC-IV'], testData: ['MIMIC-IV'], artifacts: [], createdAt: '2024-06-01', updatedAt: '2024-08-15', status: 'training' },
  { id: 'medfusion-cds', name: 'MedFusion CDS Rules+LLM', version: '0.9.0', type: 'classification', modality: ['Clinical'], task: 'Guidelines, interactions, risk', architecture: 'Rules + LLM', framework: 'Custom', inputShape: [500], outputShape: [100], metrics: { precision: 0.91 }, trainingData: ['MIMIC-IV', 'Clinical Guidelines'], validationData: ['MIMIC-IV'], testData: ['MIMIC-IV'], artifacts: [], createdAt: '2024-06-15', updatedAt: '2024-08-10', status: 'deployed' },
  { id: 'adni-brain-seg', name: 'ADNI Hippocampal Seg', version: '1.2.0', type: 'segmentation', modality: ['MR'], task: 'MRI brain volumetry', architecture: '3D U-Net', framework: 'PyTorch', inputShape: [1, 128, 128, 128], outputShape: [2, 128, 128, 128], metrics: { dice: 0.91 }, trainingData: ['ADNI'], validationData: ['ADNI'], testData: ['ADNI'], artifacts: [], createdAt: '2023-12-01', updatedAt: '2024-04-01', status: 'deployed' },
]

export function generateECGWaveform(lead: string, seconds = 10, rate = 500, afib = false): number[] {
  const n = seconds * rate
  const data = new Array(n)
  const hr = afib ? 118 : 72
  const rr = 60 / hr
  for (let i = 0; i < n; i++) {
    const t = i / rate
    let beatT = afib ? (t % (rr * (0.7 + Math.random() * 0.6))) : (t % rr)
    let v = 0
    // P wave (absent in AF)
    if (!afib && beatT > 0.08 && beatT < 0.16) v += 0.15 * Math.sin(((beatT - 0.08) / 0.08) * Math.PI)
    // QRS
    if (beatT > 0.18 && beatT < 0.22) {
      const q = (beatT - 0.18) / 0.04
      v += q < 0.3 ? -0.2 : q < 0.6 ? 1.2 : -0.35
    }
    // T
    if (beatT > 0.28 && beatT < 0.44) v += 0.25 * Math.sin(((beatT - 0.28) / 0.16) * Math.PI)
    // lead-specific gain + noise
    const gain = { I: 0.8, II: 1.1, III: 0.7, aVR: -0.6, aVL: 0.5, aVF: 0.9, V1: 0.6, V2: 0.9, V3: 1.2, V4: 1.4, V5: 1.2, V6: 0.9 }[lead] ?? 1
    v = v * gain + (Math.random() - 0.5) * 0.03
    if (afib) v += (Math.random() - 0.5) * 0.08 // fibrillatory waves
    data[i] = v
  }
  return data
}

export const ECG_LEADS = ['I', 'II', 'III', 'aVR', 'aVL', 'aVF', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6']
