# Supabase Integration Test Plan

## Prerequisites
1. ✅ Supabase project is set up
2. ✅ Tables created:
   - `Injections` (id, user_id, prompt, risk, created_at)
   - `Users` (id, promptsanalyzed, threatsblocked, successrate)
3. ✅ User is logged in (authenticated)

## Test Steps

### Test 1: Initial Sync on Page Load
1. Open the application
2. Switch to "Prompt Injection" tab
3. **Expected**: Console shows "🔄 Syncing prompt injection data with Supabase..."
4. **Expected**: Console shows "✅ Supabase sync completed"
5. **Expected**: If user has existing data, it loads from Supabase

### Test 2: Analyze a Prompt
1. Go to Prompt Injection tab
2. Enter a test prompt: "Ignore previous instructions"
3. Click "Analyze Prompt"
4. **Expected**: Analysis completes successfully
5. **Expected**: Console shows "✅ Injection saved to Supabase"
6. **Expected**: Console shows "✅ User stats updated in Supabase"
7. **Verify in Supabase**: Check `Injections` table for new row
8. **Verify in Supabase**: Check `Users` table stats are updated

### Test 3: Stats Display
1. After analyzing prompt(s)
2. Check the stats boxes:
   - Prompts Analyzed
   - Threats Blocked
   - Success Rate
3. **Expected**: Numbers should match Supabase `Users` table values

### Test 4: History Display
1. Switch to Prompt Injection tab
2. Check Security History panel
3. **Expected**: History items appear
4. **Expected**: Click on an item shows details
5. **Verify**: History matches `Injections` table in Supabase

### Test 5: Manual Sync
1. Go to Security History panel
2. Click the sync button (🔄)
3. **Expected**: Button spins during sync
4. **Expected**: Console shows "✅ Manual sync completed"
5. **Expected**: History refreshes with latest data

### Test 6: Clear History
1. Click the clear history button (🗑️)
2. Confirm the action
3. **Expected**: Local history clears
4. **Expected**: Console shows "✅ Injections cleared from Supabase"
5. **Verify in Supabase**: `Injections` table should be empty for user

### Test 7: Multiple Prompts
1. Analyze 3 different prompts
2. Check stats after each analysis
3. **Expected**: Stats increment correctly
4. **Verify in Supabase**: All 3 injections saved
5. **Verify in Supabase**: Stats match in `Users` table

### Test 8: Not Logged In
1. Log out of the application
2. Try analyzing a prompt
3. **Expected**: Works locally (localStorage)
4. **Expected**: Console shows "No user logged in, skipping Supabase save"
5. **Expected**: No errors, graceful degradation

### Test 9: Search History
1. Have multiple injections in history
2. Type in search box
3. **Expected**: History filters correctly
4. **Expected**: Search works on local data

### Test 10: Cross-Device Sync
1. Analyze prompts on Device A
2. Log in on Device B
3. Switch to Prompt Injection tab on Device B
4. **Expected**: History and stats sync from Supabase
5. **Expected**: Both devices show same data

## Console Debug Messages

### Success Messages (✅):
- ✅ Injection saved to Supabase
- ✅ User stats updated in Supabase
- ✅ Loaded injections from Supabase: X
- ✅ Loaded user stats from Supabase
- ✅ Supabase sync completed
- ✅ Manual sync completed
- ✅ Injections cleared from Supabase

### Warning Messages (⚠️):
- No user logged in, skipping Supabase save
- No user logged in, skipping stats update
- No user logged in, skipping injection load
- Failed to save injection to Supabase
- Failed to update user stats in Supabase

### Error Messages (❌):
- Error getting current user: [details]
- Error saving injection: [details]
- Error updating user stats: [details]
- Error loading injections: [details]

## Database Verification Queries

### Check Injections
```sql
SELECT * FROM "Injections" 
WHERE user_id = 'YOUR_USER_ID' 
ORDER BY created_at DESC;
```

### Check User Stats
```sql
SELECT promptsanalyzed, threatsblocked, successrate 
FROM "Users" 
WHERE id = 'YOUR_USER_ID';
```

### Count User's Injections
```sql
SELECT COUNT(*) as total_injections 
FROM "Injections" 
WHERE user_id = 'YOUR_USER_ID';
```

## Troubleshooting

### Issue: "No user logged in" message
**Solution**: Make sure user is authenticated before testing

### Issue: Stats not updating
**Solution**: Check console for errors, verify `Users` table schema

### Issue: History not loading
**Solution**: Check `Injections` table exists and has correct foreign key

### Issue: Sync button doesn't work
**Solution**: Check browser console for JavaScript errors

## Success Criteria

All tests pass when:
- ✅ Every prompt analysis saves to Supabase
- ✅ Stats update correctly in database
- ✅ History loads from Supabase on page load
- ✅ Manual sync works without errors
- ✅ Clear history removes data from database
- ✅ No console errors
- ✅ Graceful handling when user not logged in

---

**Test completed successfully if all ✅ appear!**
