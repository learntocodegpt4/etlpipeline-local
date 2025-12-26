# User Story: Rule Engine for FWC Awards Management

## Epic
Implement comprehensive Rule Engine microservice for FWC awards validation, compilation, and tenant assignment with complete filtering and customization capabilities.

---

## User Story
**As a** System Admin and Tenant Admin  
**I want** a Rule Engine that compiles, validates, and manages FWC awards with all possible combinations  
**So that** I can assign compliant awards to tenants and staff, customize pay rates while maintaining FWC compliance, and validate all assignments against official rules.

---

## Acceptance Criteria

### 1. Award Compilation & Output Generation
- [ ] System compiles all 156 awards with ALL possible combinations
- [ ] Output includes: pay rates, clauses, penalties, conditions, classifications, allowances
- [ ] Each award shows complete details in normalized, queryable format
- [ ] Compilation generates hierarchical rule codes (e.g., 01.01.001, 01.01.002)

### 2. Award Listing & Filtering
- [ ] System provides list of all available awards
- [ ] Each award displays summary information (code, name, industry type, total rules)
- [ ] Detailed view shows: pay rates, clauses, penalties, conditions for specific award
- [ ] Filtering supports: award code, industry type, classification level, penalty type, pay multiplier range
- [ ] API responses include pagination for large datasets

### 3. Input Validation & Rule Processing
- [ ] System validates award assignments when System Admin assigns to Tenant
- [ ] System validates award assignments when Tenant Admin assigns to Staff
- [ ] Validation checks: FWC compliance, classification matching, rate validity, condition applicability
- [ ] Real-time validation feedback to UI with specific error messages

### 4. FWC Compliance Confirmation
- [ ] System confirms all assigned awards comply with current FWC rules
- [ ] Validation report shows: rules applied, compliance status, any warnings/errors
- [ ] System tracks which FWC clauses apply to each assignment
- [ ] Audit trail of validation results

### 5. Multi-Award & Custom Rate Management
- [ ] System allows multiple awards per tenant
- [ ] System validates compatibility of multiple awards (no conflicts)
- [ ] Custom pay rates validated against FWC minimums
- [ ] System tracks custom rates as multipliers or overrides
- [ ] Audit history of all customizations per tenant/staff

### 6. Assignment Tracking & Reporting
- [ ] System records what awards assigned to each staff member
- [ ] System records what awards assigned to each tenant
- [ ] Reports show: original FWC rates vs customized rates
- [ ] Query API to retrieve assignment history

---

## Technical Requirements

### Database Tables
1. **TblCompiledRules** - Normalized award rules (implemented)
2. **TblTenantAwards** - Awards assigned to tenants (NEW)
3. **TblStaffAwards** - Awards assigned to staff (NEW)
4. **TblCustomPayRates** - Customized pay rates per tenant (NEW)
5. **TblAwardValidationLog** - Validation audit trail (NEW)
6. **TblAwardAssignmentHistory** - Assignment change history (NEW)

### Stored Procedures
1. **sp_CompileAwardRules** - Compile awards into rules (implemented)
2. **sp_ValidateAwardAssignment** - Validate award assignment (NEW)
3. **sp_ValidateCustomPayRate** - Validate custom rate against FWC minimum (NEW)
4. **sp_AssignAwardToTenant** - Assign award with validation (NEW)
5. **sp_AssignAwardToStaff** - Assign award to staff with validation (NEW)
6. **sp_GetTenantAwardsSummary** - Get all awards for tenant (NEW)
7. **sp_GetStaffAwardsSummary** - Get all awards for staff (NEW)

### REST API Endpoints (Rule Engine)

#### Award Compilation
- `POST /api/ruleengine/compile` - Compile all awards or specific award
- `GET /api/ruleengine/compilation-status` - Get compilation status and statistics

#### Award Query & Filtering
- `GET /api/awards/list` - Get list of all awards with summary
- `GET /api/awards/{awardCode}` - Get detailed award information
- `GET /api/awards/{awardCode}/rules` - Get all rules for specific award
- `GET /api/awards/{awardCode}/payrates` - Get all pay rates with conditions
- `GET /api/awards/{awardCode}/penalties` - Get all penalties
- `GET /api/awards/{awardCode}/clauses` - Get all applicable clauses
- `GET /api/awards/filter` - Filter awards by multiple criteria

#### Assignment Validation
- `POST /api/validation/validate-assignment` - Validate award assignment before saving
- `POST /api/validation/validate-custom-rate` - Validate custom pay rate
- `POST /api/validation/validate-multi-awards` - Validate multiple award compatibility
- `GET /api/validation/fwc-compliance/{awardCode}` - Check FWC compliance status

#### Tenant Management
- `POST /api/tenants/{tenantId}/awards` - Assign award to tenant
- `GET /api/tenants/{tenantId}/awards` - Get all awards for tenant
- `PUT /api/tenants/{tenantId}/awards/{awardCode}` - Update award assignment
- `DELETE /api/tenants/{tenantId}/awards/{awardCode}` - Remove award from tenant
- `GET /api/tenants/{tenantId}/awards/summary` - Get summary with customizations

#### Staff Management
- `POST /api/staff/{staffId}/awards` - Assign award to staff
- `GET /api/staff/{staffId}/awards` - Get all awards for staff
- `PUT /api/staff/{staffId}/awards/{awardCode}` - Update staff award
- `DELETE /api/staff/{staffId}/awards/{awardCode}` - Remove award from staff
- `GET /api/staff/{staffId}/applicable-rates` - Get applicable pay rates for staff

#### Custom Rate Management
- `POST /api/custom-rates` - Create custom pay rate for tenant
- `GET /api/custom-rates/tenant/{tenantId}` - Get all custom rates for tenant
- `PUT /api/custom-rates/{rateId}` - Update custom rate
- `DELETE /api/custom-rates/{rateId}` - Remove custom rate
- `GET /api/custom-rates/validate` - Validate custom rate against FWC minimum

#### Reporting & Audit
- `GET /api/reports/tenant-assignments` - Report of all tenant assignments
- `GET /api/reports/staff-assignments` - Report of all staff assignments
- `GET /api/reports/customizations` - Report of all customizations
- `GET /api/audit/validation-history` - Audit trail of validations
- `GET /api/audit/assignment-history` - History of assignments

---

## Tasks Breakdown

### Phase 1: Database Schema & Stored Procedures (Week 1)
**Task 1.1:** Create new database tables
- [ ] TblTenantAwards (tenant_id, award_code, assigned_by, assigned_at, is_active)
- [ ] TblStaffAwards (staff_id, award_code, tenant_id, assigned_by, assigned_at)
- [ ] TblCustomPayRates (rate_id, tenant_id, award_code, rule_code, original_rate, custom_rate, multiplier, reason)
- [ ] TblAwardValidationLog (log_id, award_code, entity_type, entity_id, validation_status, issues_json, validated_at)
- [ ] TblAwardAssignmentHistory (history_id, entity_type, entity_id, award_code, action, details_json, created_at)
- Add indexes for performance

**Task 1.2:** Create validation stored procedures
- [ ] sp_ValidateAwardAssignment - Check FWC compliance, classification match, conditions
- [ ] sp_ValidateCustomPayRate - Validate custom rate >= FWC minimum
- [ ] sp_ValidateMultiAwardCompatibility - Check for conflicts between multiple awards

**Task 1.3:** Create assignment stored procedures
- [ ] sp_AssignAwardToTenant - Assign with validation and logging
- [ ] sp_AssignAwardToStaff - Assign to staff with tenant context
- [ ] sp_GetTenantAwardsSummary - Retrieve all awards for tenant with customizations
- [ ] sp_GetStaffAwardsSummary - Retrieve all awards for staff

**Task 1.4:** Create reporting stored procedures
- [ ] sp_GetAssignmentHistory - Audit trail query
- [ ] sp_GetCustomRateReport - Report on customizations
- [ ] sp_GetValidationReport - Validation statistics

### Phase 2: .NET Domain Models & Entities (Week 1)
**Task 2.1:** Create domain entities
- [ ] TenantAward.cs - Tenant award assignment entity
- [ ] StaffAward.cs - Staff award assignment entity
- [ ] CustomPayRate.cs - Custom rate entity
- [ ] AwardValidationResult.cs - Validation result model
- [ ] AssignmentHistory.cs - History tracking entity

**Task 2.2:** Create DTOs for API requests/responses
- [ ] AssignAwardRequest.cs
- [ ] ValidateAssignmentRequest.cs
- [ ] CustomRateRequest.cs
- [ ] AwardSummaryResponse.cs
- [ ] ValidationResultResponse.cs

### Phase 3: CQRS Commands & Handlers (Week 2)
**Task 3.1:** Validation commands
- [ ] ValidateAwardAssignmentCommand + Handler
- [ ] ValidateCustomPayRateCommand + Handler
- [ ] ValidateMultiAwardsCommand + Handler

**Task 3.2:** Assignment commands
- [ ] AssignAwardToTenantCommand + Handler
- [ ] AssignAwardToStaffCommand + Handler
- [ ] UpdateAwardAssignmentCommand + Handler
- [ ] RemoveAwardAssignmentCommand + Handler

**Task 3.3:** Custom rate commands
- [ ] CreateCustomPayRateCommand + Handler
- [ ] UpdateCustomPayRateCommand + Handler
- [ ] DeleteCustomPayRateCommand + Handler

### Phase 4: CQRS Queries & Handlers (Week 2)
**Task 4.1:** Award query handlers
- [ ] GetAwardListQuery + Handler (all awards with summary)
- [ ] GetAwardDetailQuery + Handler (specific award with all details)
- [ ] GetAwardRulesQuery + Handler (all rules for award)
- [ ] GetAwardPayRatesQuery + Handler (pay rates with conditions)
- [ ] FilterAwardsQuery + Handler (multi-criteria filtering)

**Task 4.2:** Assignment query handlers
- [ ] GetTenantAwardsQuery + Handler
- [ ] GetStaffAwardsQuery + Handler
- [ ] GetAssignmentHistoryQuery + Handler

**Task 4.3:** Report query handlers
- [ ] GetTenantAssignmentReportQuery + Handler
- [ ] GetStaffAssignmentReportQuery + Handler
- [ ] GetCustomizationReportQuery + Handler
- [ ] GetValidationHistoryQuery + Handler

### Phase 5: REST API Controllers (Week 3)
**Task 5.1:** Awards controller enhancements
- [ ] GET /api/awards/list - List all awards
- [ ] GET /api/awards/{awardCode} - Award details
- [ ] GET /api/awards/{awardCode}/rules - Award rules
- [ ] GET /api/awards/filter - Filter awards

**Task 5.2:** Validation controller (new)
- [ ] POST /api/validation/validate-assignment - Validate assignment
- [ ] POST /api/validation/validate-custom-rate - Validate custom rate
- [ ] POST /api/validation/validate-multi-awards - Validate multiple awards
- [ ] GET /api/validation/fwc-compliance/{awardCode} - FWC compliance check

**Task 5.3:** Tenant awards controller (new)
- [ ] POST /api/tenants/{tenantId}/awards - Assign to tenant
- [ ] GET /api/tenants/{tenantId}/awards - Get tenant awards
- [ ] PUT /api/tenants/{tenantId}/awards/{awardCode} - Update assignment
- [ ] DELETE /api/tenants/{tenantId}/awards/{awardCode} - Remove assignment

**Task 5.4:** Staff awards controller (new)
- [ ] POST /api/staff/{staffId}/awards - Assign to staff
- [ ] GET /api/staff/{staffId}/awards - Get staff awards
- [ ] PUT /api/staff/{staffId}/awards/{awardCode} - Update staff award
- [ ] GET /api/staff/{staffId}/applicable-rates - Get applicable rates

**Task 5.5:** Custom rates controller (new)
- [ ] POST /api/custom-rates - Create custom rate
- [ ] GET /api/custom-rates/tenant/{tenantId} - Get tenant custom rates
- [ ] PUT /api/custom-rates/{rateId} - Update custom rate
- [ ] DELETE /api/custom-rates/{rateId} - Delete custom rate

**Task 5.6:** Reports controller (new)
- [ ] GET /api/reports/tenant-assignments - Tenant assignment report
- [ ] GET /api/reports/staff-assignments - Staff assignment report
- [ ] GET /api/reports/customizations - Customization report
- [ ] GET /api/audit/validation-history - Validation audit
- [ ] GET /api/audit/assignment-history - Assignment audit

### Phase 6: Repository Implementation (Week 3)
**Task 6.1:** Update IRuleEngineRepository interface
- [ ] Add methods for tenant award operations
- [ ] Add methods for staff award operations
- [ ] Add methods for custom rate operations
- [ ] Add methods for validation operations

**Task 6.2:** Implement repository methods
- [ ] Implement tenant award CRUD operations
- [ ] Implement staff award CRUD operations
- [ ] Implement custom rate CRUD operations
- [ ] Implement validation query methods
- [ ] Implement reporting query methods

### Phase 7: Business Logic & Validation (Week 4)
**Task 7.1:** FWC compliance validation logic
- [ ] Validate pay rate >= FWC minimum
- [ ] Validate classification applicability
- [ ] Validate condition logic (age, employment type, shift type)
- [ ] Validate penalty calculations

**Task 7.2:** Multi-award compatibility logic
- [ ] Check for conflicting awards
- [ ] Validate overlapping classifications
- [ ] Ensure no contradictory conditions

**Task 7.3:** Custom rate validation logic
- [ ] Calculate FWC minimum for given conditions
- [ ] Validate custom rate against minimum
- [ ] Calculate effective multiplier
- [ ] Generate validation warnings/errors

### Phase 8: Unit Tests (Week 4)
**Task 8.1:** Domain model tests
- [ ] Test entity validation
- [ ] Test business rules
- [ ] Test value objects

**Task 8.2:** Command handler tests
- [ ] Test validation commands with mock repository
- [ ] Test assignment commands
- [ ] Test custom rate commands
- [ ] Test error scenarios

**Task 8.3:** Query handler tests
- [ ] Test award query handlers
- [ ] Test assignment query handlers
- [ ] Test report query handlers

**Task 8.4:** Controller tests
- [ ] Test all API endpoints
- [ ] Test request validation
- [ ] Test error responses
- [ ] Test pagination

**Task 8.5:** Integration tests
- [ ] Test database operations
- [ ] Test stored procedure calls
- [ ] Test end-to-end scenarios

### Phase 9: Documentation (Week 5)
**Task 9.1:** API documentation
- [ ] Update Swagger documentation
- [ ] Add request/response examples
- [ ] Document validation rules
- [ ] Add error code reference

**Task 9.2:** User guides
- [ ] System Admin guide for award assignment
- [ ] Tenant Admin guide for staff assignment
- [ ] Guide for custom rate setup
- [ ] Troubleshooting guide

**Task 9.3:** Technical documentation
- [ ] Database schema documentation
- [ ] Stored procedure documentation
- [ ] Architecture decision records
- [ ] Deployment guide updates

### Phase 10: UI Integration (Week 5)
**Task 10.1:** Award listing component
- [ ] Create award list page with filtering
- [ ] Add award detail view
- [ ] Add search functionality

**Task 10.2:** Assignment workflow components
- [ ] Tenant award assignment modal
- [ ] Staff award assignment modal
- [ ] Validation feedback display
- [ ] Assignment confirmation dialog

**Task 10.3:** Custom rate management
- [ ] Custom rate creation form
- [ ] Rate comparison view (FWC vs custom)
- [ ] Validation indicator
- [ ] Customization history view

**Task 10.4:** Reporting dashboards
- [ ] Tenant assignment summary dashboard
- [ ] Staff assignment report
- [ ] Customization audit report
- [ ] Validation history report

---

## Additional Features to Consider

### Enhancement 1: Rule Versioning
- Track FWC award version changes
- Maintain history of rule compilations
- Allow comparison between versions
- Notify tenants of FWC updates

### Enhancement 2: Bulk Operations
- Bulk assign awards to multiple tenants
- Bulk update custom rates
- Bulk validation for imports
- Export/import award configurations

### Enhancement 3: Advanced Filtering
- Saved filter presets
- Complex filter combinations (AND/OR)
- Filter by effective date ranges
- Filter by assignment status

### Enhancement 4: Notifications
- Notify when FWC rules change
- Alert on validation failures
- Notify on custom rate expiry
- Assignment confirmation emails

### Enhancement 5: Analytics
- Award utilization metrics
- Customization trend analysis
- Compliance score by tenant
- Most used awards report

---

## Definition of Done

- [ ] All database tables created with proper indexes
- [ ] All stored procedures implemented and tested
- [ ] All API endpoints implemented with Swagger documentation
- [ ] Unit tests achieve >80% code coverage
- [ ] Integration tests pass for all scenarios
- [ ] Validation logic correctly enforces FWC compliance
- [ ] UI components integrated and functional
- [ ] Performance benchmarks met (<100ms API response time)
- [ ] Security review completed
- [ ] Documentation complete and reviewed
- [ ] Code review approved
- [ ] Deployed to staging environment
- [ ] User acceptance testing passed

---

## Dependencies

- ETL Pipeline must load all 156 awards data
- Database must have all staging tables populated
- FWC API access for latest award data
- Authentication/Authorization system for tenant/staff context

---

## Risks & Mitigation

**Risk 1:** FWC rules complexity
- Mitigation: Start with simple awards, iterate to complex ones

**Risk 2:** Performance with large datasets
- Mitigation: Implement caching, pagination, database optimization

**Risk 3:** Validation logic errors
- Mitigation: Comprehensive unit tests, FWC rule verification

**Risk 4:** Multi-award conflicts
- Mitigation: Clear conflict resolution rules, System Admin override capability

---

## Success Metrics

- 100% of FWC awards compiled successfully
- <100ms API response time for 95% of requests
- 0 invalid assignments pass validation
- System Admin can assign awards in <30 seconds
- Tenant Admin can assign to staff in <20 seconds
- >95% user satisfaction with validation feedback
- Zero FWC compliance violations

---

## Timeline

- **Week 1:** Database schema, stored procedures, domain models
- **Week 2:** CQRS commands, queries, handlers
- **Week 3:** REST API controllers, repository implementation
- **Week 4:** Business logic, validation, unit tests
- **Week 5:** Documentation, UI integration, deployment

**Total Duration:** 5 weeks

---

## Notes

- All code must follow SOLID principles and Clean Architecture
- Use CQRS pattern for separation of concerns
- Implement comprehensive error handling and logging
- Ensure all operations are auditable
- Design for horizontal scalability (70k users)
- Follow security best practices for multi-tenant architecture
