'use client';

import { useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Tabs,
  Tab,
  Paper,
} from '@mui/material';
import AwardsTab from '@/components/ruleengine/AwardsTab';
import AwardsDetailedTab from '@/components/ruleengine/AwardsDetailedTab';
import CalculatedPayRatesTab from '@/components/ruleengine/CalculatedPayRatesTab';
import PenaltiesTab from '@/components/ruleengine/PenaltiesTab';
import PenaltiesStatisticsTab from '@/components/ruleengine/PenaltiesStatisticsTab';
import CompilationTab from '@/components/ruleengine/CompilationTab';
import RulesTab from '@/components/ruleengine/RulesTab';

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
      id={`ruleengine-tabpanel-${index}`}
      aria-labelledby={`ruleengine-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

export default function RuleEnginePage() {
  const [activeTab, setActiveTab] = useState(0);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  return (
    <Container maxWidth={false}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Rule Engine Management
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Manage FWC awards, compile rules, view pay rates, and access all Rule Engine functionality
        </Typography>
      </Box>

      <Paper sx={{ width: '100%' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs
            value={activeTab}
            onChange={handleTabChange}
            aria-label="rule engine tabs"
            variant="scrollable"
            scrollButtons="auto"
          >
            <Tab label="Awards" id="ruleengine-tab-0" />
            <Tab label="Awards Detailed" id="ruleengine-tab-1" />
            <Tab label="Calculated Pay Rates" id="ruleengine-tab-2" />
            <Tab label="Penalties" id="ruleengine-tab-3" />
            <Tab label="Penalties Stats" id="ruleengine-tab-4" />
            <Tab label="Rules" id="ruleengine-tab-5" />
            <Tab label="Compilation" id="ruleengine-tab-6" />
          </Tabs>
        </Box>

        <TabPanel value={activeTab} index={0}>
          <AwardsTab />
        </TabPanel>
        <TabPanel value={activeTab} index={1}>
          <AwardsDetailedTab />
        </TabPanel>
        <TabPanel value={activeTab} index={2}>
          <CalculatedPayRatesTab />
        </TabPanel>
        <TabPanel value={activeTab} index={3}>
          <PenaltiesTab />
        </TabPanel>
        <TabPanel value={activeTab} index={4}>
          <PenaltiesStatisticsTab />
        </TabPanel>
        <TabPanel value={activeTab} index={5}>
          <RulesTab />
        </TabPanel>
        <TabPanel value={activeTab} index={6}>
          <CompilationTab />
        </TabPanel>
      </Paper>
    </Container>
  );
}
