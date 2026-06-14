export interface ApiResponse<T = unknown> {
  code: number;
  data: T;
  message: string;
}

export interface PaginatedResponse<T> {
  code: number;
  data: {
    items: T[];
    total: number;
    cursor: string | null;
  };
  message: string;
}

export interface College {
  id: string;
  name: string;
  aliases: string[];
}

export interface Course {
  id: string;
  name: string;
  collegeId: string;
  aliases: string[];
  semesters: string[];
}

export type TrustStatus = 'maintainer_picked' | 'community_verified' | 'unverified' | 'doubtful';

export type MaterialCategory =
  | 'lecture_notes'
  | 'exam_papers'
  | 'homework'
  | 'lab_report'
  | 'code'
  | 'textbook'
  | 'review_guide'
  | 'other';

export interface Material {
  id: string;
  title: string;
  description: string;
  courseId: string;
  collegeId: string;
  semester: string;
  category: MaterialCategory;
  format: string;
  sourceType: 'uploaded' | 'external_link';
  tags: string[];
  trustStatus: TrustStatus;
  contributorId: string;
  createdAt: string;
  updatedAt: string;
  version: number;
}
