#!/usr/bin/env python3
"""Script to analyze database schema and provide insights for RPC functions."""

import asyncio
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase_client import get_supabase

async def analyze_schema():
    print('🔍 Database Schema Analysis for RPC Functions')
    supabase = get_supabase()
    
    # Query to get column information
    schema_query = """
    SELECT 
        table_name,
        column_name,
        data_type,
        udt_name,
        is_nullable
    FROM information_schema.columns 
    WHERE table_schema = 'public' 
    AND table_name IN ('projects', 'documents', 'requirements', 'organizations', 'test_req')
    AND column_name IN ('status', 'priority', 'type', 'visibility')
    ORDER BY table_name, column_name;
    """
    
    try:
        result = supabase.rpc('exec_sql', {'sql': schema_query}).execute()
        print('📊 Column Type Information:')
        
        for row in result.data:
            table = row['table_name']
            column = row['column_name'] 
            data_type = row['data_type']
            udt_name = row['udt_name']
            nullable = row['is_nullable']
            
            print(f'   {table}.{column}:')
            print(f'      data_type: {data_type}')
            print(f'      udt_name: {udt_name}')
            print(f'      nullable: {nullable}')
            print()
            
    except Exception as e:
        print(f'❌ Schema query failed: {e}')
        print('\n🔄 Trying alternative approach...')
        
        # Alternative: Check actual enum types
        enum_query = """
        SELECT 
            t.typname as enum_name,
            e.enumlabel as enum_value
        FROM pg_type t 
        JOIN pg_enum e ON t.oid = e.enumtypid  
        WHERE t.typname LIKE '%status%' OR t.typname LIKE '%priority%' OR t.typname LIKE '%type%'
        ORDER BY t.typname, e.enumsortorder;
        """
        
        try:
            enum_result = supabase.rpc('exec_sql', {'sql': enum_query}).execute()
            print('📋 Enum Types Found:')
            
            current_enum = None
            for row in enum_result.data:
                enum_name = row['enum_name']
                enum_value = row['enum_value']
                
                if enum_name != current_enum:
                    print(f'\n   {enum_name}:')
                    current_enum = enum_name
                print(f'      - {enum_value}')
                
        except Exception as e2:
            print(f'❌ Enum query also failed: {e2}')
            
    # Get sample values to understand the actual data
    print('\n📝 Sample Values Analysis:')
    tables = ['projects', 'documents', 'requirements', 'organizations']
    
    for table in tables:
        try:
            sample = supabase.table(table).select('*').limit(1).execute()
            if sample.data:
                record = sample.data[0]
                print(f'\n   {table} sample:')
                
                for key, value in record.items():
                    if any(keyword in key.lower() for keyword in ['status', 'priority', 'type', 'visibility']):
                        print(f'      {key}: {repr(value)} ({type(value).__name__})')
                        
        except Exception as e:
            print(f'   ❌ {table}: {e}')

    print('\n💡 Recommended RPC Function Fixes:')
    print('   1. Remove all filter comparisons with enum columns')
    print('   2. Only include enum columns in metadata (not in WHERE clauses)')
    print('   3. Cast enum columns to text in jsonb_build_object')

if __name__ == "__main__":
    asyncio.run(analyze_schema())