# AI Finance Assistant - QA Deployment Architecture (Cost-Optimized)

## Overview

This document outlines a cost-optimized AWS deployment strategy for QA environments, reducing infrastructure costs by **80%** compared to the production architecture while maintaining full functional testing capability.

---

## 1. QA vs Production Architecture Comparison

```
COMPARISON MATRIX:
┌─────────────────────────────┬──────────────────┬──────────────────┐
│ Component                   │ Production       │ QA (Min Cost)    │
├─────────────────────────────┼──────────────────┼──────────────────┤
│ Availability Zones          │ Multi-AZ (2-3)   │ Single-AZ        │
│ Load Balancer               │ ALB + 443        │ Single ALB/NLB   │
│ ECS Tasks                   │ Min:2, Max:10    │ Min:1, Max:2     │
│ Task CPU/Memory             │ 256-512/1024MB   │ 256/512MB        │
│ RDS Instances               │ Multi-AZ Aurora  │ Single t3.micro  │
│ DocumentDB                  │ Multi-AZ 3-nodes │ Single instance  │
│ DynamoDB                    │ On-demand        │ Provisioned 5 RCU│
│ ElastiCache                 │ Multi-node Redis │ Single node      │
│ OpenSearch                  │ 3 nodes t3.small │ 1 node t3.small  │
│ NAT Gateways                │ 2 (HA)           │ 1 (or EC2-based) │
│ CloudFront                  │ Enabled          │ Disabled         │
│ S3 Replication              │ Cross-region     │ Single region    │
│ Backups                     │ Daily 7-day      │ Weekly 7-day     │
│ CloudWatch Logs             │ 30-day retention │ 7-day retention  │
│ WAF Rules                   │ Full             │ Basic            │
│ X-Ray Tracing               │ Full             │ Disabled         │
│ SQS/SNS                     │ Full messaging   │ Limited/In-memory│
│ VPC Endpoints               │ Multiple         │ None (internet)  │
└─────────────────────────────┴──────────────────┴──────────────────┘
```

---

## 2. QA-Optimized AWS Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         QA DEPLOYMENT ARCHITECTURE                           │
│                    (Single-AZ, Minimal Services)                            │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                    FRONTEND LAYER (SIMPLIFIED)                         │ │
│  │  Simple ALB (No CloudFront)                                           │ │
│  │  Route 53 (Direct DNS)                                                │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                 │                                           │
│                                 ▼                                           │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                    APPLICATION LAYER                                   │ │
│  │  ECS Fargate (1-2 Tasks Only)                                         │ │
│  │  • Single ALB (no multi-AZ)                                           │ │
│  │  • Minimal health checks                                              │ │
│  │                                                                        │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                 │                                           │
│     ┌───────────────────────────┼───────────────────────────┐              │
│     ▼                           ▼                           ▼              │
│  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐  │
│  │   DATA LAYER    │    │ CACHE & MESSAGING│    │   STORAGE LAYER     │  │
│  │ (SINGLE ZONE)   │    │ (SIMPLIFIED)     │    │ (MINIMAL)           │  │
│  │                 │    │                  │    │                     │  │
│  │ • RDS t3.micro  │    │ • ElastiCache    │    │ • S3 (Standard)    │  │
│  │   Single instance│   │   Single node    │    │   No replication   │  │
│  │                 │    │   (no failover)  │    │                     │  │
│  │ • DynamoDB      │    │                  │    │ • OpenSearch       │  │
│  │   Provisioned   │    │ • In-memory Queue│    │   Single node      │  │
│  │   (5 RCU)       │    │   (if SQS not ok)│    │   (no multi-AZ)    │  │
│  │                 │    │                  │    │                     │  │
│  │ • DocumentDB    │    │                  │    │ • CloudWatch Logs  │  │
│  │   Single t3.micro    │                  │    │   7-day retention  │  │
│  │   (no replica)  │    │                  │    │                     │  │
│  └─────────────────┘    └──────────────────┘    └─────────────────────┘  │
│                                                                              │
│     ┌───────────────────────────┬───────────────────────────┐              │
│     ▼                           ▼                           ▼              │
│  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐  │
│  │   SECURITY      │    │ MONITORING       │    │ EXTERNAL APIS       │  │
│  │ (MINIMAL)       │    │ (BASIC)          │    │                     │  │
│  │                 │    │                  │    │ • Claude/Gemini API │  │
│  │ • Secrets Mgr   │    │ • CloudWatch     │    │   (External)        │  │
│  │   (API Keys)    │    │   Basic metrics  │    │                     │  │
│  │                 │    │   (Errors only)  │    │ • Alpha Vantage     │  │
│  │ • Single SG     │    │                  │    │ • yFinance          │  │
│  │   (Basic rules) │    │ • SNS Alerts     │    │ • News APIs         │  │
│  │                 │    │   (Email only)   │    │                     │  │
│  │ • No WAF        │    │                  │    │                     │  │
│  │ • No KMS        │    │ • No X-Ray       │    │                     │  │
│  │   (default keys)│    │ • No dashboards  │    │                     │  │
│  └─────────────────┘    └──────────────────┘    └─────────────────────┘  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. QA Deployment VPC Layout

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              AWS ACCOUNT (QA)                                │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                        VPC (10.0.0.0/16)                               │ │
│  │                    Single Availability Zone                            │ │
│  │                                                                        │ │
│  │  ┌──────────────────────────────────────────────────────────────────┐ │ │
│  │  │                    PUBLIC SUBNET                               │ │ │
│  │  │  • Single NAT Gateway (or NAT Instance to save $$$)            │ │ │
│  │  │  • ALB                                                         │ │ │
│  │  └──────────────────────────────────────────────────────────────────┘ │ │
│  │                                                                        │ │
│  │  ┌──────────────────────────────────────────────────────────────────┐ │ │
│  │  │              PRIVATE SUBNET - APPLICATION TIER                │ │ │
│  │  │  ┌────────────────────────────────────────────────────────────┐ │ │ │
│  │  │  │  ALB (Single Instance)                                    │ │ │ │
│  │  │  └──────────────────┬─────────────────────────────────────────┘ │ │ │
│  │  │                     │                                            │ │ │
│  │  │  ┌──────────────────┴──────────────────────────────────────┐  │ │ │
│  │  │  │  ECS Fargate (1 Task, up to 2)                         │  │ │ │
│  │  │  │  • Orchestrator + 6 Agents (combined or separate)      │  │ │ │
│  │  │  │  • 256 CPU, 512 MB Memory                              │  │ │ │
│  │  │  └────────────────────────────────────────────────────────┘  │ │ │
│  │  │                                                               │ │ │
│  │  └──────────────────────────────────────────────────────────────┘ │ │
│  │                                                                        │ │
│  │  ┌──────────────────────────────────────────────────────────────────┐ │ │
│  │  │              PRIVATE SUBNET - DATA TIER                      │ │ │
│  │  │  ┌──────────────┬────────────────┬──────────────────────────┐  │ │ │
│  │  │  │ RDS t3.micro │ DocumentDB     │ DynamoDB              │  │ │ │
│  │  │  │ Single       │ Single t3.micro│ Provisioned (5 RCU)   │  │ │ │
│  │  │  │ (no replica) │ (no replica)   │                       │  │ │ │
│  │  │  └──────────────┴────────────────┴──────────────────────────┘  │ │ │
│  │  │                                                                │ │ │
│  │  │  ┌──────────────┬────────────────┬──────────────────────────┐  │ │ │
│  │  │  │ ElastiCache  │ OpenSearch     │ S3 Bucket             │  │ │ │
│  │  │  │ Single node  │ Single node    │ (Standard, no replic) │  │ │ │
│  │  │  │ (cache.t3)   │ (t3.small)     │                       │  │ │ │
│  │  │  └──────────────┴────────────────┴──────────────────────────┘  │ │ │
│  │  │                                                                │ │ │
│  │  └──────────────────────────────────────────────────────────────────┘ │ │
│  │                                                                        │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

Key Optimizations:
• Single AZ only (no NAT pair, no multi-AZ replicas)
• Smaller instance types across all services
• Reduced redundancy (no failover replicas)
• Simplified monitoring and logging
• No advanced features (WAF, X-Ray, CloudFront)
```

---

## 4. Cost Comparison

| Service | Production | QA (Optimized) | Savings |
|---------|-----------|----------------|---------|
| **ECS Fargate** | $45 (3 tasks) | $15 (1 task) | 67% |
| **ALB** | $25 | $16 (single) | 36% |
| **RDS Aurora** | $150 (multi-AZ) | $15 (t3.micro) | 90% |
| **DocumentDB** | $200 (multi-AZ) | $30 (t3.micro) | 85% |
| **DynamoDB** | $25 (on-demand) | $8 (provisioned) | 68% |
| **ElastiCache** | $20 (single) | $10 (t3.micro) | 50% |
| **OpenSearch** | $100 (3 nodes) | $15 (single) | 85% |
| **S3** | $10 (with replication) | $5 (standard) | 50% |
| **CloudWatch** | $30 | $5 (basic) | 83% |
| **Data Transfer** | $1 | $0.50 | 50% |
| **NAT Gateway** | $60 (2 x $30) | $15 (1 x $15) | 75% |
| **Route 53** | $2 | $2 | 0% |
| **Secrets Manager** | $1 | $1 | 0% |
| **Eliminated: CloudFront** | — | Saves $20 | — |
| **Eliminated: CodePipeline** | — | Use manual deploys | Saves ~$5 |
| **Total Estimated** | **$670/month** | **$132/month** | **~80% savings** |

**Notes:**
- QA environment: ~$132/month (80% reduction)
- Still supports all functional testing
- Can scale to 2 tasks if load testing needed
- Databases can be paused during off-hours for additional savings

---

## 5. Recommended QA Architecture Options

### **Option A: Highly Cost-Optimized (Recommended for MVP QA)**
```
├─ Single ECS Fargate task (256 CPU, 512 MB)
├─ Single RDS t3.micro PostgreSQL
├─ DynamoDB with provisioned capacity (5 RCU/5 WCU)
├─ Single ElastiCache t3.micro Redis
├─ Single OpenSearch t3.small node
├─ S3 (standard, no replication)
├─ No CloudFront, WAF, or X-Ray
├─ Email-only alerts from CloudWatch
├─ Manual backups (weekly snapshots)
└─ Estimated Cost: $130-150/month
```

### **Option B: Balanced (If more concurrent testing needed)**
```
├─ 2 ECS Fargate tasks (256 CPU, 512 MB each)
├─ RDS t3.small PostgreSQL (single instance)
├─ DynamoDB with provisioned capacity (10 RCU/10 WCU)
├─ Single ElastiCache t3.micro Redis
├─ Single OpenSearch t3.small node
├─ S3 (standard, no replication)
├─ Basic monitoring (error rate only)
├─ Weekly manual backups
└─ Estimated Cost: $180-200/month
```

### **Option C: Stop-on-Idle (Ultra-cheap for non-continuous testing)**
```
├─ Scheduled stop/start (8am-6pm only)
├─ Option A services
├─ RDS auto-stop after 15 min inactivity
├─ Lambda function to stop all services at 6pm
├─ Start via manual trigger or scheduled (8am)
└─ Estimated Cost: $30-50/month (80% reduction from Option A)
```

---

## 6. QA Deployment Checklist (Simplified)

### **Phase 1: Infrastructure Setup (2-3 days)**

```
1. VPC & Networking (Simplified)
   ├─ Create VPC (10.0.0.0/16)
   ├─ Create 1 public subnet
   ├─ Create 1 private subnet
   ├─ Single NAT Gateway
   ├─ Single Route Table
   └─ Basic Security Groups (3 total)

2. Secrets Management
   ├─ Store API keys in Secrets Manager
   └─ No rotation policies needed (manual is ok)

3. IAM & Permissions
   ├─ Create ECS Task Execution Role
   ├─ Create ECS Task Role
   └─ Basic policies (no fine-grained RBAC needed)
```

### **Phase 2: Data Layer (2-3 days)**

```
4. RDS PostgreSQL (t3.micro)
   ├─ Single instance (no multi-AZ)
   ├─ 20 GB storage (auto-scaling enabled)
   ├─ Basic backups (weekly manual)
   └─ No read replicas

5. DynamoDB (Provisioned)
   ├─ 5 RCU, 5 WCU
   ├─ No global secondary indexes needed
   └─ Basic TTL for session cleanup

6. DocumentDB (t3.micro)
   ├─ Single instance
   ├─ Daily automatic backups (7 days)
   └─ No replicas

7. ElastiCache Redis (t3.micro)
   ├─ Single node
   ├─ No multi-AZ failover
   └─ Basic parameter group

8. OpenSearch (t3.small, single node)
   ├─ Single data node
   ├─ 10 GB storage
   ├─ No multi-AZ
   └─ Manual snapshots to S3 (weekly)

9. S3
   ├─ Single bucket (standard tier)
   ├─ No versioning (save on storage)
   ├─ No replication
   └─ 30-day lifecycle (delete old logs)
```

### **Phase 3: Application Layer (1-2 days)**

```
10. ECR
    ├─ Create 1-2 ECR repos (combined agents possible)
    └─ No image scanning needed

11. ECS Fargate
    ├─ Create 1 cluster
    ├─ Create 1 task definition (256 CPU, 512 MB)
    ├─ Create 1 service (desired: 1, min: 1, max: 2)
    └─ Logging to CloudWatch (7-day retention)

12. ALB (Single instance)
    ├─ Single ALB
    ├─ Single target group
    ├─ Basic health checks (30s interval)
    └─ Self-signed SSL or skip HTTPS for internal testing

13. Route 53
    └─ Create A record pointing to ALB (or use IP directly)
```

### **Phase 4: Monitoring (0.5 day)**

```
14. CloudWatch
    ├─ Create basic log group (7-day retention)
    ├─ Create 2-3 critical alarms only
    │  ├─ Error rate > 10%
    │  ├─ Database connection failures
    │  └─ Out of memory
    ├─ SNS email notifications (no PagerDuty)
    └─ No custom dashboards

15. Manual Testing Setup
    ├─ Document test procedures
    ├─ Create simple test data scripts
    └─ Set up manual log review process
```

---

## 7. Cost-Saving Strategies

### **Strategy 1: Scheduled Downtime ($30-50/month)**
- Stop all services outside testing hours (6pm-8am)
- Lambda function to stop RDS, ECS, OpenSearch at 6pm
- Lambda function to start services at 8am
- **Savings: 67% on compute costs**

### **Strategy 2: Right-Sizing Instances**
- Start with t3.micro for all databases
- Monitor actual usage
- Only upgrade if needed (usually not needed for QA)
- **Savings: Built-in**

### **Strategy 3: Eliminate Redundancy**
- No multi-AZ (single-AZ only)
- No read replicas
- No cross-region replication
- No failover (manual intervention if failure)
- **Savings: ~50% on database costs**

### **Strategy 4: Simplified Monitoring**
- No X-Ray ($5-10/month)
- No advanced dashboards
- Error logs only (not all logs)
- Email alerts instead of PagerDuty
- **Savings: ~$25/month**

### **Strategy 5: On-Demand Backups**
- Manual weekly snapshots instead of daily
- No automated point-in-time recovery
- Accept loss of last week's data if failure
- **Savings: ~$5-10/month**

### **Strategy 6: Data Transfer Optimization**
- Keep everything in same region
- No cross-region data transfer
- Cache data locally in ECS tasks
- **Savings: ~$1/month (minimal)**

**Total Potential Savings: 80-85% vs Production**

---

## 8. Trade-offs & Limitations

```
QA Environment Limitations:
├─ NO automatic failover (manual intervention required)
├─ NO geographic redundancy
├─ NO high availability guarantee
├─ NO automatic scaling for load tests (2 tasks max)
├─ NO distributed tracing (debugging harder)
├─ NO advanced monitoring (manual log review)
├─ NO backup automation (manual snapshots)
├─ ACCEPTABLE data loss: up to 1 week
├─ ACCEPTABLE downtime: 30 minutes (manual recovery)
└─ USE CASE: QA testing only, NOT suitable for production

When to Upgrade to Production Architecture:
✓ When moving to production
✓ When supporting >10 concurrent users
✓ When SLA requires <99.5% uptime
✓ When business-critical data loss is unacceptable
✓ When need for geographic distribution
```

---

## 9. QA-to-Production Migration Path

```
Phase 1: QA Testing (Current)
└─ Cost: $130-150/month (single-AZ, no redundancy)

Phase 2: Staging (Pre-Production Validation)
├─ Duplicate QA infrastructure
├─ Keep in same region
├─ Cost: ~$260/month (2x QA cost)
└─ Duration: 2-4 weeks

Phase 3: Production (Full HA)
├─ Deploy multi-AZ architecture
├─ Add redundancy and failover
├─ Enable all monitoring
├─ Cost: $670/month (5x QA cost)
└─ Duration: Ongoing

---

## Available AWS Resources

Here is the list of services mentioned in the policy:

1. **EC2** (`ec2:*`)
2. **EC2 Instance Connect** (`ec2-instance-connect:*`)
3. **Billing Console** (Various `billing:` actions)
4. **Account Information** (`account:GetAccountInformation`)
5. **Cost Explorer (CE)** (Various `ce:` actions)
6. **SageMaker** (`sagemaker:ListDomains`)
7. **Consolidated Billing** (Various `consolidatedbilling:` actions)
8. **Cost and Usage Reports (CUR)** (Various `cur:` actions)
9. **Free Tier** (Various `freetier:` actions)
10. **Invoicing** (Various `invoicing:` actions)
11. **Payments** (Various `payments:` actions)
12. **Tax** (Various `tax:` actions)
13. **RDS** (`rds:*`)
14. **S3** (`s3:*`)
15. **ECR** (`ecr:*`)
16. **ECR Public** (`ecr-public:*`)
17. **Glue** (`glue:*`)
18. **IAM** (`iam:*`)


Rollback Plan (if issues found):
├─ Keep QA environment running
├─ Use QA for hotfix testing
├─ Use blue/green deployment in production
├─ Can rollback to previous version in <5 minutes
```

---

## 10. Minimal Monitoring & Alerting

### **Critical Metrics (Monitor only)**
```
├─ Error rate (log only, no alert)
├─ ECS task status (email if down)
├─ Database connectivity (manual check daily)
└─ Cost spike (manual review weekly)
```

### **Alert Rules**
```
├─ IF ECS task status = STOPPED
│  └─ THEN send email to QA team
├─ IF RDS status = CREATE_FAILED
│  └─ THEN send email to QA team
└─ IF error_rate > 50% for 5 minutes
   └─ THEN send email to QA team
```

### **Manual Checks (Daily)**
```
├─ Review CloudWatch Logs for errors
├─ Check ECS task health
├─ Verify database connectivity
└─ Spot check agent responses
```

### **Weekly Review**
```
├─ AWS cost analysis
├─ Performance baseline
├─ Test coverage report
└─ Issues & blockers
```

---

## Summary

This QA-optimized architecture provides **minimal-cost deployment** while maintaining full functionality:
- ✅ **80% cost reduction** vs production ($130-150 vs $670)
- ✅ **Single-AZ deployment** eliminates multi-AZ overhead
- ✅ **Smaller instance types** (t3.micro/small) reduce compute
- ✅ **Simplified monitoring** (errors only, no X-Ray)
- ✅ **Manual operations** acceptable for QA environment
- ✅ **No redundancy required** for testing purposes
- ✅ **Scalable to production** when ready
- ✅ **Optional auto-stop** for ultra-cheap testing (<$50/month)
