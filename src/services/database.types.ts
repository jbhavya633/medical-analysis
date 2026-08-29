export type Json = string | number | boolean | null | { [key: string]: Json | undefined } | Json[]

export interface Database {
  public: {
    Tables: {
      patients: {
        Row: {
          id: string
          mrn: string
          first_name: string
          last_name: string
          date_of_birth: string
          sex: string
          admission_id: string | null
          admission_type: string | null
          admission_date: string | null
          discharge_date: string | null
          location: string | null
          attending_physician: string | null
          created_at: string
          updated_at: string
        }
        Insert: Omit<Database['public']['Tables']['patients']['Row'], 'created_at' | 'updated_at'>
        Update: Partial<Database['public']['Tables']['patients']['Insert']>
      }
      lab_results: {
        Row: {
          id: string
          patient_id: string
          test_name: string
          value: number
          unit: string
          reference_range_low: number
          reference_range_high: number
          reference_range_unit: string
          interpretation: 'normal' | 'high' | 'low' | 'critical'
          delta: number | null
          collected_at: string
          resulted_at: string
          specimen_type: string
          panel: string
          created_at: string
        }
        Insert: Omit<Database['public']['Tables']['lab_results']['Row'], 'created_at'>
        Update: Partial<Database['public']['Tables']['lab_results']['Insert']>
      }
      imaging_studies: {
        Row: {
          id: string
          patient_id: string
          modality: 'CT' | 'MR' | 'XRAY' | 'US' | 'PET' | 'MG' | 'CR' | 'DX'
          body_part: string
          description: string
          status: 'preliminary' | 'final' | 'amended'
          study_date: string
          accession_number: string
          referring_physician: string | null
          ai_findings: Json | null
          created_at: string
          updated_at: string
        }
        Insert: Omit<Database['public']['Tables']['imaging_studies']['Row'], 'created_at' | 'updated_at'>
        Update: Partial<Database['public']['Tables']['imaging_studies']['Insert']>
      }
      imaging_series: {
        Row: {
          id: string
          study_id: string
          series_number: number
          modality: 'CT' | 'MR' | 'XRAY' | 'US' | 'PET' | 'MG' | 'CR' | 'DX'
          body_part: string
          description: string
          instance_count: number
          slice_thickness: number | null
          spacing: Json | null
          created_at: string
        }
        Insert: Omit<Database['public']['Tables']['imaging_series']['Row'], 'created_at'>
        Update: Partial<Database['public']['Tables']['imaging_series']['Insert']>
      }
      imaging_instances: {
        Row: {
          id: string
          series_id: string
          instance_number: number
          sop_instance_uid: string
          rows: number
          columns: number
          bits_allocated: number
          pixel_spacing: Json | null
          image_position: Json | null
          image_orientation: Json | null
          window_center: number | null
          window_width: number | null
          rescale_intercept: number | null
          rescale_slope: number | null
          metadata: Json | null
          ai_annotations: Json | null
          storage_path: string
          created_at: string
        }
        Insert: Omit<Database['public']['Tables']['imaging_instances']['Row'], 'created_at'>
        Update: Partial<Database['public']['Tables']['imaging_instances']['Insert']>
      }
      ecg_studies: {
        Row: {
          id: string
          patient_id: string
          rhythm: string
          heart_rate: number
          pr_interval: number
          qrs_duration: number
          qt_interval: number
          qtc_interval: number
          p_axis: number
          qrs_axis: number
          t_axis: number
          acquired_at: string
          device: string
          leads: Json
          measurements: Json
          ai_analysis: Json | null
          storage_path: string | null
          created_at: string
        }
        Insert: Omit<Database['public']['Tables']['ecg_studies']['Row'], 'created_at'>
        Update: Partial<Database['public']['Tables']['ecg_studies']['Insert']>
      }
      clinical_notes: {
        Row: {
          id: string
          patient_id: string
          type: 'progress' | 'discharge' | 'admission' | 'consult' | 'procedure' | 'nursing'
          title: string
          content: string
          author: string
          author_role: string
          created_at: string
          updated_at: string
          tags: string[]
        }
        Insert: Omit<Database['public']['Tables']['clinical_notes']['Row'], 'created_at' | 'updated_at'>
        Update: Partial<Database['public']['Tables']['clinical_notes']['Insert']>
      }
      medications: {
        Row: {
          id: string
          patient_id: string
          name: string
          dose: string
          route: string
          frequency: string
          indication: string
          status: 'active' | 'discontinued' | 'held'
          start_date: string
          end_date: string | null
          prescriber: string
          created_at: string
        }
        Insert: Omit<Database['public']['Tables']['medications']['Row'], 'created_at'>
        Update: Partial<Database['public']['Tables']['medications']['Insert']>
      }
      conditions: {
        Row: {
          id: string
          patient_id: string
          code: string
          display: string
          system: string
          category: string
          severity: 'mild' | 'moderate' | 'severe' | 'critical'
          status: 'active' | 'resolved' | 'inactive'
          onset_date: string
          resolved_date: string | null
          created_at: string
        }
        Insert: Omit<Database['public']['Tables']['conditions']['Row'], 'created_at'>
        Update: Partial<Database['public']['Tables']['conditions']['Insert']>
      }
      ai_insights: {
        Row: {
          id: string
          patient_id: string
          type: 'diagnosis' | 'risk' | 'treatment' | 'monitoring' | 'anomaly'
          title: string
          summary: string
          priority: 'low' | 'medium' | 'high' | 'critical'
          confidence: number
          model_id: string
          evidence: Json
          recommendations: string[]
          status: 'new' | 'reviewed' | 'accepted' | 'dismissed'
          reviewed_by: string | null
          reviewed_at: string | null
          created_at: string
        }
        Insert: Omit<Database['public']['Tables']['ai_insights']['Row'], 'created_at'>
        Update: Partial<Database['public']['Tables']['ai_insights']['Insert']>
      }
      risk_scores: {
        Row: {
          id: string
          patient_id: string
          name: string
          category: string
          score: number
          threshold: number
          percentile: number
          time_horizon: string
          model_id: string
          factors: Json
          computed_at: string
        }
        Insert: Omit<Database['public']['Tables']['risk_scores']['Row'], 'computed_at'>
        Update: Partial<Database['public']['Tables']['risk_scores']['Insert']>
      }
      vitals: {
        Row: {
          id: string
          patient_id: string
          heart_rate: number | null
          spo2: number | null
          systolic_bp: number | null
          diastolic_bp: number | null
          temperature: number | null
          respiratory_rate: number | null
          timestamp: string
          source: string
        }
        Insert: Omit<Database['public']['Tables']['vitals']['Row'], 'id'>
        Update: Partial<Database['public']['Tables']['vitals']['Insert']>
      }
      models: {
        Row: {
          id: string
          name: string
          task: string
          modality: 'ecg' | 'imaging' | 'clinical' | 'fusion'
          dataset: string
          architecture: string
          parameters: string
          version: string
          status: 'training' | 'deployed' | 'archived'
          metrics: Json
          training_config: Json
          deployed_at: string | null
          created_at: string
        }
        Insert: Omit<Database['public']['Tables']['models']['Row'], 'created_at'>
        Update: Partial<Database['public']['Tables']['models']['Insert']>
      }
      datasets: {
        Row: {
          id: string
          name: string
          role: string
          modality: string[]
          status: 'download' | 'processing' | 'ready' | 'credentialed'
          size_gb: number
          record_count: number
          description: string
          source_url: string
          credential_required: boolean
          created_at: string
        }
        Insert: Omit<Database['public']['Tables']['datasets']['Row'], 'created_at'>
        Update: Partial<Database['public']['Tables']['datasets']['Insert']>
      }
      ai_jobs: {
        Row: {
          id: string
          patient_id: string
          modalities: string[]
          task: string
          status: 'pending' | 'running' | 'completed' | 'failed'
          progress: number
          result: Json | null
          error: string | null
          started_at: string | null
          completed_at: string | null
          created_at: string
        }
        Insert: Omit<Database['public']['Tables']['ai_jobs']['Row'], 'created_at'>
        Update: Partial<Database['public']['Tables']['ai_jobs']['Insert']>
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      lab_interpretation: 'normal' | 'high' | 'low' | 'critical'
      imaging_modality: 'CT' | 'MR' | 'XRAY' | 'US' | 'PET' | 'MG' | 'CR' | 'DX'
      imaging_status: 'preliminary' | 'final' | 'amended'
      ecg_rhythm: string
      note_type: 'progress' | 'discharge' | 'admission' | 'consult' | 'procedure' | 'nursing'
      medication_status: 'active' | 'discontinued' | 'held'
      condition_severity: 'mild' | 'moderate' | 'severe' | 'critical'
      condition_status: 'active' | 'resolved' | 'inactive'
      insight_type: 'diagnosis' | 'risk' | 'treatment' | 'monitoring' | 'anomaly'
      insight_priority: 'low' | 'medium' | 'high' | 'critical'
      insight_status: 'new' | 'reviewed' | 'accepted' | 'dismissed'
      model_modality: 'ecg' | 'imaging' | 'clinical' | 'fusion'
      model_status: 'training' | 'deployed' | 'archived'
      dataset_status: 'download' | 'processing' | 'ready' | 'credentialed'
      job_status: 'pending' | 'running' | 'completed' | 'failed'
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}