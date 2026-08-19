# Django E-Commerce Multi-Vendor Role-Based Access Control Implementation Plan

## Executive Summary
This project requires implementing a secure role-based access control system for a Django e-commerce platform with proper vendor approval workflows, product ownership isolation, and multi-vendor order visibility.

---

## 1. Current Architecture Analysis

### Models
- **CustomUser**: AbstractBaseUser with role field (customer/vendor/admin)
  - Has `role` and `is_approved` fields but no status tracking
  - Missing: vendor_status (pending/approved/rejected/suspended)
  - Missing: approved_at, approved_by, suspended_at timestamps
  
- **Product**: ForeignKey to CustomUser as vendor
  - Also has domain (SiteProfile) and site (SiteProfile) - redundant
  - Missing: proper ownership validation on save/edit
  
- **Order**: ForeignKey to CustomUser
  
- **VendorOrder**: Good structure - links Order to Vendor
  
- **OrderItem**: Links to VendorOrder and Product
  
- **SiteProfile**: OneToOne to Site, has store_name, store_logo
  - Not linked to user (should be)

### Authentication Flow
- CustomUser with email as USERNAME_FIELD
- Role-based routing in panel_login
- Basic approval check in vendor_dashboard

### Security Issues
1. **No vendor status differentiation** - only approved/not approved
2. **Template-only authorization** - checks in templates, not backend
3. **No IDOR protection** - vendors can access URLs with other vendor IDs
4. **Weak product filtering** - relies on template checks
5. **No authorization mixins/decorators** - copied auth checks everywhere
6. **No cache invalidation** - stale data risks
7. **No pagination** - scalability issues with large datasets

---

## 2. Proposed Changes

### 2.1 Model Changes

#### Option A: Extend CustomUser (Recommended for simplicity)
Add to CustomUser:
```python
VENDOR_STATUS_CHOICES = [
    ('not_vendor', 'Not a Vendor'),      # Default for customers
    ('pending', 'Pending Approval'),      # Awaiting admin review
    ('approved', 'Approved'),             # Can access vendor panel
    ('rejected', 'Rejected'),             # Application rejected
    ('suspended', 'Suspended'),           # Temporarily disabled
]

vendor_status = CharField(max_length=20, choices=VENDOR_STATUS_CHOICES, default='not_vendor')
approved_at = DateTimeField(null=True, blank=True)
approved_by = ForeignKey(CustomUser, null=True, blank=True, on_delete=SET_NULL, related_name='approved_vendors')
rejection_reason = TextField(null=True, blank=True)
suspended_at = DateTimeField(null=True, blank=True)
```

#### Option B: Create VendorProfile Model
```python
class VendorProfile(Model):
    user = OneToOneField(CustomUser, on_delete=CASCADE, related_name='vendor_profile')
    status = CharField(...)
    store_name = CharField(...)
    store_logo = ImageField(...)
    approved_at = DateTimeField(...)
    approved_by = ForeignKey(CustomUser, ...)
    rejection_reason = TextField(...)
```

**Decision**: Use Option A (extend CustomUser) because:
- Simpler implementation
- No additional queries needed
- Already has is_approved, just extend it
- Existing migrations can be extended

### 2.2 Authorization Architecture

Create reusable authorization system:

```python
# app/auth_decorators.py
def vendor_required(view_func):
    """Requires vendor role and approved status"""
    
def admin_required(view_func):
    """Requires admin role"""
    
def vendor_or_admin(view_func):
    """Vendor (approved) or admin"""
```

Create object-level authorization:

```python
# app/auth_helpers.py
def can_access_product(user, product):
    """Check if user can edit/delete product"""
    
def can_access_vendor_order(user, vendor_order):
    """Check if user can view vendor order"""
    
def can_view_order_items(user, order):
    """Check if user can view order items"""
```

### 2.3 Order System Updates

Current VendorOrder structure is good. Ensure:
- Vendors see only their VendorOrder instances
- Use `VendorOrder.objects.filter(vendor=request.user)`
- Admins see all orders with all items
- OrderItem filtering based on product vendor

### 2.4 Cache Strategy

**Public Cached:**
- Product listings (with cache invalidation on product change)
- Store profiles (invalidate on update)
- Category listings (invalidate on change)

**Private (Not Cached):**
- Vendor dashboards
- Admin dashboards
- User orders/profiles
- Personalized data

**Implementation:**
- Use Django's cache framework
- Cache key pattern: `product_{id}`, `products_shop_{site_id}`, `categories_{site_id}`
- Invalidate on post_save/post_delete signals

---

## 3. Implementation Steps

### Phase 1: Model Changes (No Breaking Changes)
1. Add vendor_status, approved_at, approved_by, rejection_reason to CustomUser
2. Create migration (reversible)
3. Create management command to migrate existing is_approved data
4. Update CustomUser methods

### Phase 2: Authorization Infrastructure
1. Create auth_decorators.py with decorator functions
2. Create auth_helpers.py with authorization checks
3. Create custom permission mixins
4. Add these to views without breaking existing ones

### Phase 3: View Updates (Backward Compatible)
1. Add authorization checks to all panel views
2. Implement IDOR checks in product/order views
3. Update vendor_dashboard to check vendor_status != 'pending'
4. Implement admin vendor management (approve/reject/suspend)

### Phase 4: Templates & UX
1. Update login to show status messages
2. Update dashboard to block pending vendors
3. Add status messages using Django messages framework
4. Create pending vendor status page

### Phase 5: Admin Features
1. Create vendor approval dashboard
2. Add reject/suspend vendor functionality
3. Filter vendors by status
4. Show approval history

### Phase 6: Cache & Optimization
1. Add cache decorators to public views
2. Implement cache invalidation on signals
3. Add pagination to admin views
4. Optimize queries with select_related/prefetch_related

### Phase 7: Testing
1. Unit tests for authorization
2. Integration tests for vendor workflows
3. Security tests for IDOR
4. Cache invalidation tests

---

## 4. Files to Create

- `app/auth_decorators.py` - Authorization decorators
- `app/auth_helpers.py` - Authorization helper functions
- `app/permissions.py` - Permission mixins and classes
- `app/cache_utils.py` - Cache helper functions
- `app/management/commands/migrate_vendor_approval.py` - Data migration
- Migration file for model changes
- Updated templates for vendor status display
- Tests for authorization

---

## 5. Files to Modify

### Models
- `app/models.py` - Extend CustomUser

### Views
- `app/views.py` - Add auth checks to all views

### Admin
- `app/admin.py` - Update CustomUser admin

### URLs
- `app/urls.py` - Add new vendor approval URLs if needed

### Settings
- `ecommerece/settings.py` - Add cache configuration

### Middleware (Optional)
- Add permission checking middleware if needed

---

## 6. Security Checklist

- [x] Backend authorization checks (not just templates)
- [x] IDOR protection on product/order access
- [x] Vendor status validation before access
- [x] Form security (no hidden vendor_id manipulation)
- [x] CSRF protection on all state-changing actions
- [x] POST for approve/reject/suspend
- [x] Transaction handling for critical ops
- [x] No N+1 queries (select_related/prefetch_related)
- [x] Cache invalidation strategy
- [x] Messages framework for user feedback
- [x] Prevent vendor role bypass
- [x] Proper on_delete behavior in ForeignKeys

---

## 7. Vendor Approval Workflow

### Flow
1. User registers with role='vendor'
2. System sets vendor_status='pending'
3. Email notification to admin (optional)
4. Admin views pending vendors in dashboard
5. Admin can:
   - Approve → vendor_status='approved', approved_at=now(), approved_by=admin_user
   - Reject → vendor_status='rejected', rejection_reason='...'
   - Suspend → vendor_status='suspended', suspended_at=now()
6. Vendor can only access panel if status='approved'
7. Pending/Rejected vendor sees status message
8. Approved vendor can create/manage products

### Messages
- Pending: "Your vendor account is pending admin approval. Please wait."
- Rejected: "Your vendor request has been rejected. Reason: {reason}"
- Approved: "Your vendor account is approved. Welcome!"
- Suspended: "Your account is temporarily suspended. Please contact admin."

---

## 8. Product Ownership Isolation

### Rules
- Product.vendor FK must match authenticated user
- Vendor can only see/edit/delete own products
- Admin can see all products
- View must validate: `get_object_or_404(Product, id=id, vendor=request.user)` for vendors
- Cannot change vendor of existing product from UI

### Implementation
- Use object-level permission checks
- QuerySet filtering: `Product.objects.filter(vendor=request.user)`
- IDOR test: Try accessing other vendor's product ID directly

---

## 9. Multi-Vendor Order Visibility

### Rules
- Order contains multiple OrderItems from different vendors
- Admin sees complete order with all items
- Vendor A sees only items where product.vendor == Vendor A
- Filter items: `order.items.filter(product__vendor=vendor)`
- Vendor cannot see entire order if they have no items in it

### Implementation
```python
# Vendor view
if request.user.role == 'admin':
    items = order.items.all()
else:
    items = order.items.filter(product__vendor=request.user)
    if not items.exists():
        raise PermissionDenied("You don't have access to this order")
```

---

## 10. Database Integrity

### Edge Cases Handled
- Vendor deleted → Products and orders stay (PROTECT)
- Product deleted → OrderItem stays (PROTECT historical)
- User changes status while logged in → Checked on each view
- Concurrent approval → Handled by transaction
- Rejected vendor reapplies → Treated as new application
- Duplicate vendor applications → Prevent via unique vendor status check

### Migrations
- Reversible where possible
- Data migration for existing vendors
- No CASCADE on important historical data

---

## 11. Performance Strategy

### Queries Optimized
- Product list: select_related('vendor', 'category')
- Orders: prefetch_related('items', 'items__product')
- Vendors: annotate with product_count, order_count
- Pagination: 25-50 items per page for admin views

### Caching
- Public product pages: 1 hour
- Store profiles: 1 hour
- Admin lists: 5 minutes
- Invalidate on create/update/delete

### Indexes
- CustomUser: (role, vendor_status)
- Product: (vendor_id)
- VendorOrder: (vendor_id, status)
- OrderItem: (product_id)

---

## 12. Testing Strategy

### Unit Tests
- Authorization decorator behavior
- Permission helper functions
- Vendor status transitions

### Integration Tests
- Pending vendor cannot access dashboard
- Approved vendor can access dashboard
- Vendor cannot see other vendor's products
- Admin can see all products

### Security Tests
- IDOR on product URLs
- IDOR on order URLs
- Cross-vendor access attempts
- URL manipulation tests

### Cache Tests
- Cache invalidation on updates
- No stale data after delete
- Public pages are cached
- Private pages not cached

---

## 13. Deployment Checklist

- [ ] Code reviewed
- [ ] Tests passing
- [ ] Migrations tested locally
- [ ] Backup database before migration
- [ ] Run migrations
- [ ] Run data migration for existing vendors
- [ ] Clear cache
- [ ] Verify login flow works
- [ ] Test vendor dashboard access
- [ ] Test admin dashboard
- [ ] Monitor for errors

---

## 14. Timeline Estimate

- Phase 1 (Models): 1-2 hours
- Phase 2 (Auth Infra): 2-3 hours
- Phase 3 (Views): 3-4 hours
- Phase 4 (Templates): 1-2 hours
- Phase 5 (Admin Features): 2-3 hours
- Phase 6 (Cache): 1-2 hours
- Phase 7 (Testing): 2-3 hours

**Total: ~15-20 hours**

---

## 15. Key Principles

1. **Security First**: No template-only checks
2. **Backward Compatible**: Existing data/functionality preserved
3. **Clean Code**: Reusable decorators/helpers, no duplication
4. **Django Native**: Use Django patterns, not custom solutions
5. **Tested**: All critical paths tested
6. **Documented**: Code comments on non-obvious logic
7. **Performant**: No N+1, proper pagination
8. **Maintainable**: Easy to extend later

---

## Next Steps

1. Run analysis on actual code
2. Create migration strategy
3. Implement Phase 1-2
4. Code review with team
5. Proceed to Phase 3+

