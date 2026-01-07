# KAI Extension v2.0 - Command Reference 📚

## Quick Start
Press `Ctrl+Shift+K` to open KAI widget, or press `V` for voice commands.

---

## 🆕 New Commands (v2.0)

### Web Scraping Commands

#### Extract Tables
```
extract table
save table as csv
save table as json
```
**What it does**: Finds all HTML tables on the page, shows row/column counts, and optionally downloads as CSV or JSON.

**Example**:
```
extract table          # Shows all tables
save table as csv      # Downloads first table as CSV
```

---

#### Extract Links
```
get all links
extract links
scrape links
```
**What it does**: Finds all hyperlinks on the page, shows first 10, auto-downloads full list as JSON.

**Output**: JSON file with `{text, url, domain}` for each link

---

#### Extract Emails
```
find emails
get all emails
extract emails
```
**What it does**: Scans page for email addresses, displays them, and copies to clipboard.

---

#### Extract Everything
```
extract data
scrape page
save page data
```
**What it does**: Comprehensive extraction - tables, links, emails, phones, products, lists, images.

**Output**: JSON file with all structured data from the page

---

### Workflow Commands

#### Run Workflow (Sequential Actions)
```
workflow: <action1>, <action2>, <action3>, ...
flow: <action1>, <action2>, ...
```

**Supported Actions**:
- `wait Ns` - Wait N seconds (e.g., `wait 2s`)
- `fill <field> with <value>` - Fill form field
- `click <button>` - Click button
- `scroll <direction>` - Scroll (top/bottom/up/down)
- `navigate <url>` - Go to URL

**Examples**:
```
workflow: fill email, click next, wait 2s, fill password, click submit
workflow: scroll bottom, wait 1s, click load more, wait 2s
flow: navigate google.com, wait 1s, fill search with AI tools, click search
```

---

#### Save Workflow
```
save workflow <name>
```
**What it does**: Saves the last executed workflow for reuse.

**Example**:
```
workflow: fill email, click next, wait 2s, submit
save workflow login_sequence
```

---

#### List Workflows
```
workflows
list workflows
show workflows
```
**What it does**: Shows all saved workflows with step counts.

---

## 📋 Existing Commands (Still Available)

### Form Filling
```
fill                      # Smart autofill all fields
autofill                  # Same as fill
fill email with john@example.com
fill #3 with test value   # Fill field by number
use my name               # Fill with profile data
use my email
fields                    # List all fields
profile                   # Show your profile
clear                     # Clear all fields
```

### Macros & Templates
```
record                    # Start recording actions
stop                      # Stop recording
stop as <name>            # Stop and save macro
play <macro>              # Play saved macro
macros                    # List saved macros
save template <name>      # Save form as template
apply template <name>     # Apply saved template
templates                 # List templates
```

### Browser Control
```
open <url>                # Open new tab
close                     # Close current tab
refresh                   # Reload page
go back                   # Navigate back
go forward                # Navigate forward
tabs                      # List all tabs
switch tab #2             # Switch to tab 2
new window                # Open new window
```

### Page Actions
```
click <button>            # Click button by text
scroll top|bottom|up|down # Scroll page
screenshot                # Take screenshot
copy url                  # Copy current URL
highlight <text>          # Find and highlight text
search <query>            # Google search
```

### Other
```
help                      # Show commands
?                         # Same as help
```

---

## 💡 Pro Tips

### Combine Commands in Workflows
Instead of running commands one by one:
```
fill email
click next
wait 2s  
fill password
click submit
```

Do it all at once:
```
workflow: fill email, click next, wait 2s, fill password, click submit
```

### Save Common Tasks
```
# First time:
workflow: navigate linkedin.com, wait 2s, fill email, fill password, click sign in
save workflow linkedin_login

# Next time:
play linkedin_login
```

### Quick Data Export
On any page with tables:
```
save table as csv         # Instant CSV download
```

On any page:
```
extract data              # Get everything as JSON
```

---

## 🎯 Real-World Examples

### Example 1: Price Comparison
```
1. Navigate to Amazon product page
2. extract data
3. Check JSON for price, title, images
4. Repeat for other sites
5. Compare prices in downloaded files
```

### Example 2: Contact Scraping
```
1. Go to company directory page
2. find emails
3. extract data  
4. Get emails from clipboard + full data from JSON
```

### Example 3: Form Testing
```
# Test a multi-step form:
workflow: fill name, fill email, click next, wait 1s, fill phone, fill address, click next, wait 1s, click submit
save workflow test_registration

# Run it 10 times with different data
```

### Example 4: Daily Task Automation
```
# Morning routine:
workflow: navigate todoist.com, wait 2s, click add task, fill task with Check emails, click add
save workflow daily_task

# Run every morning
```

---

## 🔍 Command Patterns

### Pattern: "extract/get/scrape + data type"
```
extract table
get links  
scrape page
find emails
```

### Pattern: "workflow: action, action, action"
```
workflow: navigate site.com, wait 2s, fill form, submit
```

### Pattern: "save X as Y"
```
save table as csv
save template work_form
save workflow my_flow
```

---

## 🚀 Advanced Usage

### Conditional Workflows (Coming Soon)
```
workflow: if button exists, click it, else wait 5s
```

### Parameterized Workflows (Coming Soon)
```
play login with email=john@test.com, password=secret
```

### Monitoring (Coming Soon)
```
monitor price
alert when stock available
```

---

## 📞 Need Help?

Type `help` in the widget to see all available commands.

**Not working?**
1. Refresh the page
2. Check console for errors (F12)
3. Reload extension
4. Verify permissions

**Still stuck?**
Check the [upgrade walkthrough](file:///C:/Users/anime/.gemini/antigravity/brain/7d2a9986-5099-456c-b8d3-866cc63bf7ae/upgrade_walkthrough.md) for detailed testing and troubleshooting.

---

**Version**: 2.0.0  
**Last Updated**: Dec 31, 2025  
**Status**: ✅ Ready to use!
