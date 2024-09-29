import json
from pathlib import Path


def get_non_list_keys(properties):
    return [key for key, value in properties.items() if not value.get('list')]


def generate_database(spec: dict):
    with open('database/schema.sql', 'w') as file:
        for key, value in spec.items():
            file.write(f'CREATE TABLE {key} (')
            for property_key, property_value in value['properties'].items():
                if property_value['type'] == 'string':
                    file.write(f'{property_key} VARCHAR(255), ')
                elif '$' in property_value['type'] and not property_value.get('list'):
                    file.write(f'{property_key} INTEGER, ')
            file.write('id SERIAL PRIMARY KEY );\n')


def generate_backend_app(spec: dict):
    with open('backend/main.py', 'w') as file:
        file.write(
'''
from fastapi import FastAPI, Request
from app import service
import uvicorn

app = FastAPI()

'''
                   )

        for key in spec.keys():
            file.writelines(
f'''
@app.get('/{key}s')
async def get_{key}s():
    return service.get_{key}s()

@app.post('/{key}s')
async def post_{key}s(request: Request):
    request = await request.json()
    return service.post_{key}s(request)

@app.get('/{key}s/{{{key}_id}}')
async def get_{key}({key}_id):
    return service.get_{key}(int({key}_id))
''')
        file.write(
'''
if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port='8000')
''')
            

def generate_backend_service(spec):
    with open('backend/app/service.py', 'w') as file:
        file.write(
'''
from app import database
'''
        )
        for key, value in spec.items():
            file.writelines(
f'''
def get_{key}s():
    return database.get_{key}s()

def post_{key}s(request):
    return database.post_{key}s(request)

def get_{key}({key}_id):
    return database.get_{key}({key}_id)
'''
            )


def generate_backend_database(spec):
    with open('backend/app/database.py', 'w') as file:
        file.write(
'''
import psycopg2

def get_connection():
    return psycopg2.connect(
        dbname='postgres',
        user='postgres',
        host='psql',
        port='5432',
        password='password')
'''
        )
        for key, value in spec.items():
            file.write(
f'''
def get_{key}s():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute('SELECT id, {', '. join(get_non_list_keys(value['properties']))} FROM {key}')
            result = cursor.fetchall()
            response = []
            for row in result:
                response.append({{ 'id': row[0], ''')
            for idx, property_key in enumerate(get_non_list_keys(value['properties'])):
                file.write(f"'{property_key}': row[{idx + 1}], ")
            file.write(
f'''
                }})
            return response
            
def post_{key}s(request):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                'INSERT INTO {key} ({', '. join(get_non_list_keys(value['properties']))}) VALUES ({', '.join('%s' for _ in get_non_list_keys(value['properties']))})',
                ({', '.join([f"request['{key}']" for key in get_non_list_keys(value['properties'])])})
            )

def get_{key}({key}_id):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute('SELECT id, {', '. join(get_non_list_keys(value['properties']))} FROM {key} WHERE id = %s', ({key}_id,))
            row = cursor.fetchone()
            return {{ 'id': row[0], ''')
            for idx, property_key in enumerate(get_non_list_keys(value['properties'])):
                file.write(f"'{property_key}': row[{idx + 1}], ")
            file.write(
'''}
''')


def generate_backend(spec: dict):
    generate_backend_app(spec)
    generate_backend_service(spec)
    generate_backend_database(spec)


def generate_frontend(spec: dict):
    filename = 'frontend/src/app/page.tsx'
    path = Path(filename)
    path.parent.mkdir(exist_ok=True, parents=True)
    with open(filename, 'w') as file:
        file.write(
'''
import Link from "next/link";

export default function Home() {
  return (
    <ul className="text-blue-400 text-4xl">
''')
        for key, value in spec.items():
            file.write(
f'''
        <li key="{key}s" className="m-8">
            <p><Link href="/{key}s">{key}s</Link></p>
        </li>
''')
        
        file.write(
'''
    </ul>
  );
}

''')

    for key, value in spec.items():
        filename = f'frontend/src/app/{key}s/page.tsx'
        path = Path(filename)
        path.parent.mkdir(exist_ok=True, parents=True)
        with open(filename, 'w') as file:
            file.write(
f'''
import Link from "next/link";

function Create{key.title()}() {{
  async function create{key.title()}(formData) {{
    "use server";
''')
            for property_key in value['properties'].keys():
                file.write(
f'''\
    const {property_key} = formData.get("{property_key}");
''')
            file.write(
f'''\
    await fetch("http://127.0.0.1:8000/{key}s", {{
      cache: "no-store",
      method: "POST",
      headers: {{
        "Content-Type": "application/json",
      }},
      body: JSON.stringify({{
''')
            for property_key in value['properties'].keys():
                file.write(
f'''\
        {property_key},
''')
            file.write(
f'''\
      }}),
    }});
  }}

  return (
    <div className="w-fit m-8">
      <form action={{create{key.title()}}}>
''')
            for property_key, property_value in value['properties'].items():
                if property_value.get('list'):
                    continue
                file.write(
f'''\
        <div className="flex justify-between space-x-4">
          <p>{property_key}:</p>
          <input name="{property_key}" className="border border-black" />
        </div>
''')
            file.write(
f'''\
        <button type="submit" className="bg-blue-500 rounded">Create New {key.title()}</button>
      </form>
    </div>
  );
}}

type {key.title()} = {{
''')
            for property_key, property_value in value['properties'].items():
                file.write(
f'''\
  {property_key}: {'number' if '$' in property_value['type'] else  property_value['type'] };
''')
            file.write(
f'''\
  id: number;
}};

function {key.title()}({{ {key} }}: {{ {key}: {key.title()} }}) {{
  return (
    <li key={{{key}.id}} className="m-8 text-xl border border-black rounded">
''')
            for property_key, property_value in value['properties'].items():
                if property_value.get('list'):
                    continue
                if '$' in property_value['type']:
                    property_type = property_value['type'][1:]
                    file.write(
f'''\
      <p><Link href={{`/{property_type}s/${{{key}.{property_type}}}`}} className="text-blue-400">
        {property_type.title()}: {{{key}.{property_type}}}
      </Link></p>
''')
                else:
                    file.write(
f'''\
      <p>{property_key.title()}: {{{key}.{property_key}}}</p>
''')
            file.write(
f'''\
      <p><Link href={{`/{key}s/${{{key}.id}}`}} className="text-blue-400">Details</Link></p>
    </li>
  );
}}

export default async function {key.title()}s() {{
  const data = await fetch("http://localhost:8000/{key}s", {{cache: "no-store"}});
  const {key}s = await data.json();
  return (
    <>
      <p className="m-8 text-4xl">{key.title()}s</p>
      <Create{key.title()} />
      <ul>
        {{{key}s.map(({key}: {key.title()}) => (
          <{key.title()} {key}={{{key}}} />
        ))}}
      </ul>
    </>
  );
}}
'''
            )
    for key, value in spec.items():
        filename = f'frontend/src/app/{key}s/[id]/page.tsx'
        path = Path(filename)
        path.parent.mkdir(exist_ok=True, parents=True)
        with open(filename, 'w') as file:
            file.write(
f'''
import Link from "next/link";

type {key.title()} = {{
''')
            for property_key, property_value in value['properties'].items():
                file.write(
f'''\
  {property_key}: {'number' if '$' in property_value['type'] else  property_value['type'] };
''')
            file.write(
f'''\
  id: number;
}};

export default async function Page({{ params }}: {{ params: {{ id: string }} }}) {{
  const data = await fetch(`http://localhost:8000/{key}s/${{params.id}}`, {{
    cache: "no-store",
  }});
  const {key}: {key.title()} = await data.json();
  return (
    <>
''')
            for property_key, property_value in value['properties'].items():
                if property_value.get('list'):
                    continue
                if '$' in property_value['type']:
                    property_type = property_value['type'][1:]
                    file.write(
f'''\
      <p><Link href={{`/{property_type}s/${{{key}.{property_type}}}`}} className="text-blue-400">
        {property_type.title()}: {{{key}.{property_type}}}
      </Link></p>
''')
                else:
                    file.write(
f'''\
      <p>{property_key.title()}: {{{key}.{property_key}}}</p>
''')
            file.write(
'''\
    </>
  );
}
''')



def main():
    with open("spec.json") as spec_file:
        spec = json.load(spec_file)
    generate_database(spec)
    generate_backend(spec)
    generate_frontend(spec)



if __name__ == '__main__':
    main()
