import { Context, Handler, param, post, route, Types } from 'hydrooj';
import { ObjectId } from 'mongodb';
import { getConfig } from './config';

interface ContestPlagiarismRequest {
  contest_id: string;
  min_tokens?: number;
  similarity_threshold?: number;
}

interface PlagiarismResult {
  analysis_id: string;
  contest_id: string;
  problem_id: number;
  total_submissions: number;
  total_comparisons: number;
  execution_time_ms: number;
  high_similarity_pairs: Array<{
    first_submission: string;
    second_submission: string;
    similarities: {
      AVG: number;
      MAX: number;
    };
  }>;
  clusters: Array<{
    index: number;
    average_similarity: number;
    strength: number;
    members: string[];
  }>;
  submission_stats: Array<{
    submission_id: string;
    display_name: string;
    file_count: number;
    total_tokens: number;
  }>;
  failed_submissions: any[];
  created_at: string;
  jplag_file_path?: string;
}

// Configuration for Phosphorus backend
const config = getConfig();

class PlagiarismMainHandler extends Handler {
  async get(domainId: string, contestId: ObjectId) {
    // Validate contestId parameter
    if (!contestId) {
      throw new this.ctx.Error('Contest ID is required');
    }

    // Validate contest exists and user has permission
    const contest = await this.ctx.db.collection('contest').findOne({ _id: contestId });
    if (!contest) {
      throw new this.ctx.Error('Contest not found');
    }

    // Check if user has permission to view plagiarism results
    this.checkPerm(this.ctx.PERM.PERM_VIEW_CONTEST_ADMIN);

    // Get existing plagiarism results for this contest
    const results = await this.getPlagiarismResults(contestId.toString());

    this.response.template = 'contest_plagiarism.html';
    this.response.body = {
      contest,
      results,
      contestId: contestId.toString(),
      title: `Plagiarism Detection - ${contest.title}`,
    };
  }

  @param('contestId', Types.ObjectId)
  @post('action', 'analyze')
  async postAnalyze(domainId: string, contestId: ObjectId) {
    // Validate contestId parameter
    if (!contestId) {
      throw new this.ctx.Error('Contest ID is required');
    }

    // Validate contest exists and user has permission
    const contest = await this.ctx.db.collection('contest').findOne({ _id: contestId });
    if (!contest) {
      throw new this.ctx.Error('Contest not found');
    }

    this.checkPerm(this.ctx.PERM.PERM_EDIT_CONTEST);

    const minTokens = parseInt(this.request.body.min_tokens, 10) || config.defaults.minTokens;
    const similarityThreshold = parseFloat(this.request.body.similarity_threshold) || config.defaults.similarityThreshold;

    // Validate parameters
    if (minTokens < 1 || minTokens > 100) {
      throw new this.ctx.Error('Invalid min_tokens value. Must be between 1 and 100.');
    }
    
    if (similarityThreshold < 0.0 || similarityThreshold > 1.0) {
      throw new this.ctx.Error('Invalid similarity_threshold value. Must be between 0.0 and 1.0.');
    }

    try {
      // Call Phosphorus backend API
      const requestData: ContestPlagiarismRequest = {
        contest_id: contestId.toString(),
        min_tokens: minTokens,
        similarity_threshold: similarityThreshold,
      };

      const result = await this.callPhosphorusAPI('/api/v1/contest/plagiarism', 'POST', requestData);

      this.response.body = {
        success: true,
        message: 'Plagiarism analysis started successfully',
        result: result.data,
      };
    } catch (error) {
      this.ctx.logger.error('Failed to start plagiarism analysis:', error);
      throw new this.ctx.Error('Failed to start plagiarism analysis', 500, error);
    }
  }

  @param('contestId', Types.ObjectId)
  @post('action', 'getResults')
  async postGetResults(domainId: string, contestId: ObjectId) {
    // Validate contestId parameter
    if (!contestId) {
      throw new this.ctx.Error('Contest ID is required');
    }

    this.checkPerm(this.ctx.PERM.PERM_VIEW_CONTEST_ADMIN);

    try {
      const results = await this.getPlagiarismResults(contestId.toString());
      this.response.body = {
        success: true,
        results,
      };
    } catch (error) {
      this.ctx.logger.error('Failed to get plagiarism results:', error);
      throw new this.ctx.Error('Failed to get plagiarism results', 500, error);
    }
  }

  private async getPlagiarismResults(contestId: string): Promise<PlagiarismResult[]> {
    if (!contestId) {
      this.ctx.logger.warn('getPlagiarismResults called with empty contestId');
      return [];
    }

    try {
      const response = await this.callPhosphorusAPI(`/api/v1/contest/${contestId}/plagiarism`, 'GET');
      return response?.data || [];
    } catch (error) {
      this.ctx.logger.warn('Failed to fetch plagiarism results:', error);
      return [];
    }
  }

  private async callPhosphorusAPI(endpoint: string, method: string, data?: any): Promise<any> {
    if (!endpoint) {
      throw new Error('API endpoint is required');
    }

    const url = `${config.baseUrl}${endpoint}`;
    const options: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: config.timeout,
    };

    if (data && method !== 'GET') {
      options.body = JSON.stringify(data);
    }

    try {
      if (config.debug) {
        this.ctx.logger.debug('Calling Phosphorus API:', { url, method, data });
      }

      const response = await fetch(url, options);

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      const result = await response.json();
      
      if (config.debug) {
        this.ctx.logger.debug('Phosphorus API response:', result);
      }

      return result;
    } catch (error) {
      this.ctx.logger.error('Phosphorus API call failed:', {
        url,
        method,
        error: error.message,
      });
      throw error;
    }
  }
}

export function apply(ctx: Context) {
  ctx.Route('contest_plagiarism', '/contest/:contestId/plagiarism', PlagiarismMainHandler);
  
  // Add menu item to contest admin page
  ctx.on('handler/contest/admin', (thisArg, args) => {
    try {
      const [domainId, contestId] = args;
      
      // Validate arguments
      if (!contestId) {
        ctx.logger.warn('Contest admin handler called without contestId');
        return;
      }

      // Check permissions before adding menu item
      if (thisArg.user && thisArg.user.hasPerm && thisArg.user.hasPerm(ctx.PERM.PERM_EDIT_CONTEST)) {
        // Ensure response body structure exists
        if (!thisArg.response.body) {
          thisArg.response.body = {};
        }
        if (!thisArg.response.body.navItems) {
          thisArg.response.body.navItems = [];
        }

        thisArg.response.body.navItems.push({
          name: 'plagiarism',
          displayName: 'Plagiarism Detection',
          args: { contestId },
          href: ctx.url('contest_plagiarism', { contestId }),
        });
      }
    } catch (error) {
      ctx.logger.error('Error in contest admin handler:', error);
    }
  });
}