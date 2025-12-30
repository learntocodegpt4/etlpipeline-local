'use client';

import { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Box,
  Grid,
  Alert,
  FormControlLabel,
  Checkbox,
  Tabs,
  Tab,
  Paper,
  Typography,
  Card,
  CardContent,
  CircularProgress,
} from '@mui/material';
import { Save, Close, Preview as PreviewIcon } from '@mui/icons-material';
import { useSnackbar } from '@/context/SnackbarContext';
import { useLoader } from '@/context/LoaderContext';
import { createRule } from '@/lib/api';

interface CreateRuleDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

interface FormErrors {
  [key: string]: string;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`rule-tabpanel-${index}`}
      aria-labelledby={`rule-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export default function CreateRuleDialog({ open, onClose, onSuccess }: CreateRuleDialogProps) {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<FormErrors>({});
  const [confirmCloseOpen, setConfirmCloseOpen] = useState(false);
  const [formData, setFormData] = useState({
    ruleCode: '',
    ruleName: '',
    ruleType: '',
    ruleCategory: '',
    priority: 0,
    isActive: true,
    createdBy: '',
    ruleExpression: '',
    ruleDefinition: '',
    applicableFrom: new Date().toISOString().split('T')[0],
    applicableTo: '',
  });

  const { showSnackbar } = useSnackbar();
  const { setIsLoading } = useLoader();

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    // Required fields
    if (!formData.ruleCode.trim()) newErrors.ruleCode = 'Rule Code is required';
    if (!formData.ruleName.trim()) newErrors.ruleName = 'Rule Name is required';
    if (!formData.ruleType.trim()) newErrors.ruleType = 'Rule Type is required';
    if (!formData.ruleCategory.trim()) newErrors.ruleCategory = 'Rule Category is required';
    if (!formData.createdBy.trim()) newErrors.createdBy = 'Created By is required';
    if (!formData.ruleExpression.trim()) newErrors.ruleExpression = 'Rule Expression is required';
    if (!formData.ruleDefinition.trim()) newErrors.ruleDefinition = 'Rule Definition is required';

    // Format validations
    if (formData.ruleCode.trim() && !/^[A-Z0-9_-]+$/.test(formData.ruleCode)) {
      newErrors.ruleCode = 'Rule Code must contain only uppercase letters, numbers, hyphens, and underscores';
    }

    if (formData.priority && (formData.priority < 0 || formData.priority > 1000)) {
      newErrors.priority = 'Priority must be between 0 and 1000';
    }

    // Date validations
    if (formData.applicableTo && formData.applicableFrom && formData.applicableTo < formData.applicableFrom) {
      newErrors.applicableTo = 'End date must be after start date';
    }

    // Expression validation (basic JSON or expression syntax check)
    if (formData.ruleExpression.trim()) {
      try {
        // Try to parse as JSON
        if (formData.ruleExpression.trim().startsWith('{')) {
          JSON.parse(formData.ruleExpression);
        }
      } catch (e) {
        newErrors.ruleExpression = 'Expression must be valid JSON or expression syntax';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target as any;
    const val = type === 'checkbox' ? (e.target as HTMLInputElement).checked : value;

    setFormData((prev) => ({
      ...prev,
      [name]: val,
    }));

    // Clear error for this field on change
    if (errors[name]) {
      setErrors((prev) => {
        const newErrs = { ...prev };
        delete newErrs[name];
        return newErrs;
      });
    }
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      showSnackbar('Please fix validation errors before submitting', 'error');
      return;
    }

    setLoading(true);
    setIsLoading(true);

    try {
      const response = await createRule({
        ruleCode: formData.ruleCode,
        ruleName: formData.ruleName,
        ruleType: formData.ruleType,
        ruleCategory: formData.ruleCategory,
        priority: Number(formData.priority),
        isActive: formData.isActive,
        createdBy: formData.createdBy,
        ruleExpression: formData.ruleExpression,
        ruleDefinition: formData.ruleDefinition,
        applicableFrom: formData.applicableFrom,
        applicableTo: formData.applicableTo || undefined,
      });

      showSnackbar('Rule created successfully', 'success');
      onSuccess?.();
      handleClose();
    } catch (error: any) {
      showSnackbar(error.message || 'Failed to create rule', 'error');
    } finally {
      setLoading(false);
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      const hasChanges = Object.values(formData).some(val => 
        val !== '' && val !== 0 && val !== true && val !== new Date().toISOString().split('T')[0]
      );
      
      if (hasChanges) {
        setConfirmCloseOpen(true);
      } else {
        clearForm();
        onClose();
      }
    }
  };

  const clearForm = () => {
    setFormData({
      ruleCode: '',
      ruleName: '',
      ruleType: '',
      ruleCategory: '',
      priority: 0,
      isActive: true,
      createdBy: '',
      ruleExpression: '',
      ruleDefinition: '',
      applicableFrom: new Date().toISOString().split('T')[0],
      applicableTo: '',
    });
    setErrors({});
    setTabValue(0);
  };

  const handleConfirmClose = (shouldClose: boolean) => {
    setConfirmCloseOpen(false);
    if (shouldClose) {
      clearForm();
      onClose();
    }
  };

  const validateExpression = () => {
    try {
      if (formData.ruleExpression.trim().startsWith('{')) {
        JSON.parse(formData.ruleExpression);
        showSnackbar('Expression is valid JSON', 'success');
      } else {
        showSnackbar('Expression format validation: passed (non-JSON format)', 'success');
      }
    } catch (e) {
      showSnackbar('Invalid expression format', 'error');
    }
  };

  return (
    <Dialog 
      open={open} 
      onClose={(event, reason) => {
        // Only allow close via the cancel button or successful submission
        if (reason === 'backdropClick' || reason === 'escapeKeyDown') {
          return;
        }
        handleClose();
      }}
      maxWidth="sm" 
      fullWidth
      disableEscapeKeyDown={true}
      PaperProps={{
        sx: { backdropFilter: 'blur(4px)' }
      }}
    >
      <DialogTitle>Create New Rule</DialogTitle>
      <DialogContent dividers>
        <Box sx={{ mt: 2 }}>
          <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
            <Tab label="Basic Info" id="rule-tab-0" aria-controls="rule-tabpanel-0" />
            <Tab label="Expression & Definition" id="rule-tab-1" aria-controls="rule-tabpanel-1" />
            <Tab label="Dates & Settings" id="rule-tab-2" aria-controls="rule-tabpanel-2" />
            <Tab label="Preview" id="rule-tab-3" aria-controls="rule-tabpanel-3" />
          </Tabs>

          {/* Tab 1: Basic Info */}
          <TabPanel value={tabValue} index={0}>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <TextField
                  label="Rule Code"
                  name="ruleCode"
                  value={formData.ruleCode}
                  onChange={handleInputChange}
                  fullWidth
                  required
                  error={!!errors.ruleCode}
                  helperText={errors.ruleCode || 'Uppercase letters, numbers, hyphens, underscores only'}
                  placeholder="e.g., RULE_001-A"
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  label="Rule Name"
                  name="ruleName"
                  value={formData.ruleName}
                  onChange={handleInputChange}
                  fullWidth
                  required
                  error={!!errors.ruleName}
                  helperText={errors.ruleName}
                  placeholder="Descriptive rule name"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Rule Type"
                  name="ruleType"
                  value={formData.ruleType}
                  onChange={handleInputChange}
                  fullWidth
                  required
                  error={!!errors.ruleType}
                  helperText={errors.ruleType || 'e.g., Penalty, Allowance, Calculation'}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Rule Category"
                  name="ruleCategory"
                  value={formData.ruleCategory}
                  onChange={handleInputChange}
                  fullWidth
                  required
                  error={!!errors.ruleCategory}
                  helperText={errors.ruleCategory || 'e.g., Award-Specific, Global'}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  label="Created By"
                  name="createdBy"
                  value={formData.createdBy}
                  onChange={handleInputChange}
                  fullWidth
                  required
                  error={!!errors.createdBy}
                  helperText={errors.createdBy}
                  placeholder="Your name or system ID"
                />
              </Grid>
            </Grid>
          </TabPanel>

          {/* Tab 2: Expression & Definition */}
          <TabPanel value={tabValue} index={1}>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <Typography variant="subtitle2">Rule Expression</Typography>
                  <Button size="small" startIcon={<PreviewIcon />} onClick={validateExpression}>
                    Validate
                  </Button>
                </Box>
                <TextField
                  label="Rule Expression"
                  name="ruleExpression"
                  value={formData.ruleExpression}
                  onChange={handleInputChange}
                  fullWidth
                  required
                  multiline
                  rows={6}
                  error={!!errors.ruleExpression}
                  helperText={errors.ruleExpression || 'JSON object or expression syntax'}
                  placeholder={JSON.stringify({ field: 'value', operator: '>', value: 100 }, null, 2)}
                  sx={{ fontFamily: 'monospace' }}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  label="Rule Definition"
                  name="ruleDefinition"
                  value={formData.ruleDefinition}
                  onChange={handleInputChange}
                  fullWidth
                  required
                  multiline
                  rows={6}
                  error={!!errors.ruleDefinition}
                  helperText={errors.ruleDefinition || 'Description of what this rule does'}
                  placeholder="Explain the business logic and conditions..."
                />
              </Grid>
            </Grid>
          </TabPanel>

          {/* Tab 3: Dates & Settings */}
          <TabPanel value={tabValue} index={2}>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Applicable From"
                  name="applicableFrom"
                  type="date"
                  value={formData.applicableFrom}
                  onChange={handleInputChange}
                  fullWidth
                  InputLabelProps={{ shrink: true }}
                  error={!!errors.applicableFrom}
                  helperText={errors.applicableFrom}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Applicable To"
                  name="applicableTo"
                  type="date"
                  value={formData.applicableTo}
                  onChange={handleInputChange}
                  fullWidth
                  InputLabelProps={{ shrink: true }}
                  error={!!errors.applicableTo}
                  helperText={errors.applicableTo || 'Leave blank for no end date'}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Priority"
                  name="priority"
                  type="number"
                  value={formData.priority}
                  onChange={handleInputChange}
                  fullWidth
                  inputProps={{ min: 0, max: 1000 }}
                  error={!!errors.priority}
                  helperText={errors.priority || 'Higher = Higher Priority (0-1000)'}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <Box sx={{ display: 'flex', alignItems: 'center', height: '100%' }}>
                  <FormControlLabel
                    control={
                      <Checkbox
                        name="isActive"
                        checked={formData.isActive}
                        onChange={handleInputChange}
                      />
                    }
                    label="Active"
                  />
                </Box>
              </Grid>
            </Grid>
          </TabPanel>

          {/* Tab 4: Preview */}
          <TabPanel value={tabValue} index={3}>
            <Box>
              <Typography variant="h6" gutterBottom>
                Rule Preview
              </Typography>
              <Card sx={{ mb: 2, bgcolor: '#f5f5f5' }}>
                <CardContent>
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                      <Typography variant="caption" color="text.secondary">
                        Code
                      </Typography>
                      <Typography variant="body2">{formData.ruleCode || 'N/A'}</Typography>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Typography variant="caption" color="text.secondary">
                        Name
                      </Typography>
                      <Typography variant="body2">{formData.ruleName || 'N/A'}</Typography>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Typography variant="caption" color="text.secondary">
                        Type
                      </Typography>
                      <Typography variant="body2">{formData.ruleType || 'N/A'}</Typography>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Typography variant="caption" color="text.secondary">
                        Category
                      </Typography>
                      <Typography variant="body2">{formData.ruleCategory || 'N/A'}</Typography>
                    </Grid>
                    <Grid item xs={12} sm={4}>
                      <Typography variant="caption" color="text.secondary">
                        Priority
                      </Typography>
                      <Typography variant="body2">{formData.priority}</Typography>
                    </Grid>
                    <Grid item xs={12} sm={4}>
                      <Typography variant="caption" color="text.secondary">
                        Active
                      </Typography>
                      <Typography variant="body2">{formData.isActive ? 'Yes' : 'No'}</Typography>
                    </Grid>
                    <Grid item xs={12} sm={4}>
                      <Typography variant="caption" color="text.secondary">
                        Created By
                      </Typography>
                      <Typography variant="body2">{formData.createdBy || 'N/A'}</Typography>
                    </Grid>
                    <Grid item xs={12}>
                      <Typography variant="caption" color="text.secondary">
                        Valid Period
                      </Typography>
                      <Typography variant="body2">
                        {formData.applicableFrom} {formData.applicableTo ? `to ${formData.applicableTo}` : '(ongoing)'}
                      </Typography>
                    </Grid>
                    <Grid item xs={12}>
                      <Typography variant="caption" color="text.secondary">
                        Expression
                      </Typography>
                      <Paper sx={{ p: 1, bgcolor: '#fff', maxHeight: 200, overflow: 'auto' }}>
                        <Typography variant="body2" component="pre" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                          {formData.ruleExpression || 'N/A'}
                        </Typography>
                      </Paper>
                    </Grid>
                    <Grid item xs={12}>
                      <Typography variant="caption" color="text.secondary">
                        Definition
                      </Typography>
                      <Paper sx={{ p: 1, bgcolor: '#fff', maxHeight: 200, overflow: 'auto' }}>
                        <Typography variant="body2">{formData.ruleDefinition || 'N/A'}</Typography>
                      </Paper>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Box>
          </TabPanel>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={loading} startIcon={<Close />}>
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={loading}
          startIcon={loading ? <CircularProgress size={20} /> : <Save />}
        >
          {loading ? 'Creating...' : 'Create Rule'}
        </Button>
      </DialogActions>
      
      {/* Confirmation dialog for unsaved changes */}
      <Dialog open={confirmCloseOpen} onClose={() => setConfirmCloseOpen(false)}>
        <DialogTitle>Discard Changes?</DialogTitle>
        <DialogContent>
          <Typography>You have unsaved changes. Are you sure you want to close without saving?</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => handleConfirmClose(false)} color="primary">
            Keep Editing
          </Button>
          <Button onClick={() => handleConfirmClose(true)} color="error" variant="contained">
            Discard
          </Button>
        </DialogActions>
      </Dialog>
    </Dialog>
  );
}
