# Rule Engine UI Implementation Guide

## Overview
This document provides complete implementation details for the Rule Engine UI, which provides a comprehensive interface to all Rule Engine API endpoints.

## Architecture

### Technology Stack
- **Frontend Framework**: Next.js 14 with App Router
- **UI Library**: Material-UI v5 (MUI) with DataGrid
- **State Management**: SWR for data fetching and caching
- **Language**: TypeScript
- **Styling**: Material-UI theming (Bootstrap-like responsiveness)

### File Structure
```
ui/src/
├── app/
│   └── ruleengine/
│       └── page.tsx                    # Main Rule Engine page with tabs
├── components/
│   └── ruleengine/
│       ├── AwardsTab.tsx               # GET /api/Awards
│       ├── AwardsDetailedTab.tsx       # GET /api/AwardsDetailed
│       ├── CalculatedPayRatesTab.tsx   # GET /api/CalculatedPayRates + POST calculate + GET statistics
│       ├── PenaltiesTab.tsx            # GET /api/Penalties + GET statistics
│       ├── RulesTab.tsx                # GET /api/Rules
│       └── CompilationTab.tsx          # POST compile-awards, compile-awards-detailed, apply-rule, GET award-rules-json
└── lib/
    └── api.ts                          # Updated with Rule Engine API hooks
```

## API Integration

### Base URL
- Default: `http://localhost:8082/api`
- Configurable via: `NEXT_PUBLIC_RULE_ENGINE_API_URL`

### Implemented Hooks

#### Awards
```typescript
useRuleEngineAwards(page, pageSize)
// Returns: { awards, totalCount, isLoading, error, mutate }
```

#### Awards Detailed
```typescript
useAwardsDetailed(awardCode?, recordType?, page, pageSize)
// Returns: { awardsDetailed, totalCount, isLoading, error, mutate }
```

#### Calculated Pay Rates
```typescript
useCalculatedPayRates(awardCode?, employmentType?, dayType?, page, pageSize)
// Returns: { payRates, totalCount, isLoading, error, mutate }

usePayRateStatistics(awardCode?)
// Returns: { statistics, isLoading, error }
```

#### Penalties
```typescript
useRuleEnginePenalties(awardCode?, classificationLevel?, page, pageSize)
// Returns: { penalties, totalCount, isLoading, error, mutate }

useRuleEnginePenaltyStatistics(awardCode?)
// Returns: { statistics, isLoading, error }
```

#### Rules
```typescript
useRules(awardCode?, type?, page, pageSize)
// Returns: { rules, totalCount, isLoading, error, mutate }
```

### Implemented API Functions

#### Compilation Functions
```typescript
compileAwards(awardCode?)
// POST /api/RuleEngine/compile-awards

compileAwardsDetailed(awardCode?)
// POST /api/RuleEngine/compile-awards-detailed

calculatePayRates(awardCode?, classificationLevel?)
// POST /api/CalculatedPayRates/calculate

applyRule(awardCode, ruleId)
// POST /api/RuleEngine/apply-rule

getAwardRulesJson(awardCode)
// GET /api/RuleEngine/award-rules-json
```

## Component Specifications

### 1. AwardsTab Component
**Purpose**: Display all FWC awards with search and filtering

**Features**:
- DataGrid with sortable columns
- Search by award code or name
- Pagination (25/50/100 records per page)
- Refresh button
- Export to CSV

**Columns**:
- Award Code
- Award Name
- Industry
- Version
- Operative From/To dates

### 2. AwardsDetailedTab Component
**Purpose**: Display detailed award information with all record types

**Features**:
- Filter by award code
- Filter by record type (BASE, WITH_CLASSIFICATION, WITH_PAYRATE, WITH_EXPENSE, WITH_WAGE)
- Show all related data (classifications, pay rates, allowances)
- Expandable rows for detailed view
- Export functionality

**Record Types Explanation**:
- **BASE**: Award metadata only (nulls in detail fields are expected)
- **WITH_CLASSIFICATION**: Classification data
- **WITH_PAYRATE**: Pay rate calculations
- **WITH_EXPENSE**: Expense allowances
- **WITH_WAGE**: Wage allowances

### 3. CalculatedPayRatesTab Component
**Purpose**: View and calculate pay rates with various conditions

**Features**:
- Filter by award code, employment type, day type
- Statistics summary card (total rates, min/max values)
- Calculate new rates button (triggers POST /calculate)
- View calculation steps
- Download calculated rates

**Columns**:
- Award Code, Classification, Employment Type
- Day Type, Shift Type, Base Rate
- Calculated Rate, Multiplier, Calculation Steps

### 4. PenaltiesTab Component
**Purpose**: Display FWC penalties data

**Features**:
- Filter by award code, classification level
- Statistics card showing total penalties
- Penalty rate percentage display
- Clause references
- Calculated penalty values

**Columns**:
- Penalty ID, Award Code, Description
- Rate (%), Calculated Value, Classification Level
- Clause Description, Base Pay Rate ID

### 5. RulesTab Component
**Purpose**: Display compiled rules

**Features**:
- Filter by award code and rule type
- View rule details (code, name, category, priority)
- JSON view for rule conditions
- Apply rule to award functionality
- Export rules as JSON

**Columns**:
- Rule Code, Rule Name, Category
- Priority, Status, Award Code
- Actions (View, Apply, Export JSON)

### 6. CompilationTab Component
**Purpose**: Trigger award compilation and processing

**Features**:
- **Compile Awards Summary**:
  - Input: Award code (optional for all awards)
  - Button: "Compile Awards"
  - Progress indicator
  - Result display (success/error, records compiled)

- **Compile Awards Detailed**:
  - Input: Award code (optional)
  - Button: "Compile Detailed"
  - Show compilation statistics
  
- **Calculate Pay Rates**:
  - Inputs: Award code, classification level (optional)
  - Button: "Calculate Rates"
  - Display calculation progress and results

- **Apply Rule**:
  - Inputs: Award code, rule ID
  - Button: "Apply Rule"
  - Show application result

- **Export Award Rules JSON**:
  - Input: Award code
  - Button: "Export JSON"
  - Download rules as JSON file

## UI/UX Design Patterns

### Layout
- Tabbed interface with 6 main tabs
- Consistent card-based layout
- Material-UI theming for professional appearance
- Responsive design (mobile, tablet, desktop)

### Common Features Across Tabs
1. **Search & Filter**:
   - Text fields for award code
   - Dropdowns for categorical filters
   - Clear filter button

2. **Data Display**:
   - Material-UI DataGrid
   - Sortable columns
   - Pagination controls
   - Row selection

3. **Actions**:
   - Refresh data button
   - Export to CSV
   - View details modal
   - Processing buttons

4. **Feedback**:
   - Loading indicators (CircularProgress)
   - Error alerts (Alert component)
   - Success messages (Snackbar)
   - Empty state messages

### Color Scheme
- Primary: Material-UI default blue
- Success: Green (#4caf50)
- Warning: Orange (#ff9800)
- Error: Red (#f44336)
- Background: Light grey (#f5f5f5)

## Deployment

### Docker Configuration

#### Dockerfile Updates
No changes needed - existing Next.js Dockerfile works.

#### Environment Variables
Add to `.env` or `docker-compose.yml`:
```
NEXT_PUBLIC_RULE_ENGINE_API_URL=http://localhost:8082/api
```

For NGINX proxy:
```
NEXT_PUBLIC_RULE_ENGINE_API_URL=/ruleapi/api
```

### Azure Pipeline

#### Build Stage
```yaml
- task: NodeTool@0
  inputs:
    versionSpec: '18.x'
- script: |
    cd ui
    npm ci
    npm run build
  displayName: 'Build Next.js UI'
```

#### Deploy Stage
```yaml
- task: Docker@2
  inputs:
    command: 'buildAndPush'
    containerRegistry: 'ACR'
    repository: 'etl-ui'
    Dockerfile: 'ui/Dockerfile'
```

### NGINX Configuration

Add Rule Engine proxy:
```nginx
location /ruleapi/ {
    proxy_pass http://ruleengine:8082/api/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_cache_bypass $http_upgrade;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

## Testing

### Unit Tests (Optional)
```typescript
// Example test for AwardsTab
describe('AwardsTab', () => {
  it('should render awards list', async () => {
    render(<AwardsTab />);
    await waitFor(() => {
      expect(screen.getByText('Awards Summary')).toBeInTheDocument();
    });
  });
});
```

### Integration Testing
1. Verify Rule Engine API is accessible
2. Test each tab loads data correctly
3. Test filtering and search functionality
4. Test compilation actions trigger correctly
5. Test export functionality works

## Troubleshooting

### Common Issues

**1. API Connection Refused**
- Check Rule Engine is running: `curl http://localhost:8082/api/Awards`
- Verify CORS settings in Rule Engine API
- Check environment variable `NEXT_PUBLIC_RULE_ENGINE_API_URL`

**2. Empty Data Displayed**
- Verify database has data: Run ETL pipeline first
- Check compilation has been run
- Verify API endpoints return data via Swagger

**3. Swagger Not Loading**
- Access directly: http://localhost:8082/swagger
- Via NGINX: http://localhost:8081/ruleapi/swagger
- Check Program.cs SwaggerGen configuration

**4. BASE Records Show NULL Values**
- This is expected! BASE records contain only award metadata
- Query other record types for detailed data:
  - WITH_CLASSIFICATION
  - WITH_PAYRATE
  - WITH_EXPENSE
  - WITH_WAGE

## Usage Workflow

### For System Admins

**Step 1: View Available Awards**
- Navigate to Rule Engine → Awards tab
- Browse all 156 FWC awards
- Search for specific award

**Step 2: Compile Award Data**
- Go to Compilation tab
- Select award code (or leave blank for all)
- Click "Compile Awards Summary"
- Wait for completion
- Click "Compile Awards Detailed"

**Step 3: Calculate Pay Rates**
- In Compilation tab, click "Calculate Pay Rates"
- Enter award code and optional classification level
- View calculation results

**Step 4: View Results**
- Go to Calculated Pay Rates tab
- Filter by award code
- View all calculated rates with conditions
- Export data if needed

**Step 5: Review Details**
- Check Awards Detailed tab for complete information
- View Penalties tab for penalty rates
- Check Rules tab for compiled rules

## API Endpoint Mapping

| UI Tab | API Endpoints Used |
|--------|-------------------|
| Awards | GET /api/Awards |
| Awards Detailed | GET /api/AwardsDetailed |
| Calculated Pay Rates | GET /api/CalculatedPayRates<br>POST /api/CalculatedPayRates/calculate<br>GET /api/CalculatedPayRates/statistics |
| Penalties | GET /api/Penalties<br>GET /api/Penalties/statistics |
| Rules | GET /api/Rules |
| Compilation | POST /api/RuleEngine/compile-awards<br>POST /api/RuleEngine/compile-awards-detailed<br>POST /api/RuleEngine/apply-rule<br>GET /api/RuleEngine/award-rules-json |

## Next Steps

### Phase 1 (Complete)
✅ Create page routing
✅ Update Layout with Rule Engine menu
✅ Add API hooks to api.ts
✅ Create AwardsTab component

### Phase 2 (To Complete)
- [ ] Create remaining component files
- [ ] Add error boundaries
- [ ] Implement loading skeletons
- [ ] Add toast notifications

### Phase 3 (Enhancement)
- [ ] Add data visualization (charts)
- [ ] Implement advanced filtering
- [ ] Add batch operations
- [ ] Create detailed modals

### Phase 4 (Production)
- [ ] Add unit tests
- [ ] Optimize performance
- [ ] Complete Azure pipeline
- [ ] Documentation updates

## Support

For issues or questions:
- Check DEPLOYMENT_OPERATIONS_GUIDE.md
- Review Swagger documentation
- Check application logs
- Verify ETL pipeline has run successfully

