import os
import json
from flask import Flask, request, jsonify
import openai

# Initialize Flask application
app = Flask(__name__)

# Initialize OpenAI API key (replace with your actual key)
openai.api_key = ""


# Function to create the folder structure based on project name and base path
def create_directory_structure(base_path, project_name):
    project_path = os.path.join(base_path, project_name)
    folders = ["model", "repository", "service", "controller"]

    # Create project folder
    if not os.path.exists(project_path):
        os.makedirs(project_path)
        print(f"Created project folder: {project_path}")

    # Create subfolders within the project folder
    for folder in folders:
        path = os.path.join(project_path, folder)
        if not os.path.exists(path):
            os.makedirs(path)
            print(f"Created {folder} folder at: {path}")

    return project_path


# Function to generate the Model class
def generate_model_class(entity, fields):
    class_template = f"package model;\n\nimport jakarta.persistence.Entity;\nimport jakarta.persistence.Id;\nimport jakarta.persistence.GeneratedValue;\nimport jakarta.persistence.GenerationType;\n\n@Entity\npublic class {entity} " + "{\n"

    # Fields
    for field, field_type in fields.items():
        if field == "id":  # Assuming the field 'id' is the primary key
            class_template += f"    @Id\n    @GeneratedValue(strategy = GenerationType.IDENTITY)\n"
        class_template += f"    private {field_type} {field};\n"

    # Constructor
    constructor_params = ", ".join([f"{field_type} {field}" for field, field_type in fields.items()])
    class_template += f"\n    public {entity}({constructor_params}) " + "{\n"
    for field in fields:
        class_template += f"        this.{field} = {field};\n"
    class_template += "    }\n"

    # Getters and Setters
    for field, field_type in fields.items():
        # Getter
        class_template += f"\n    public {field_type} get{field.capitalize()}() {{\n"
        class_template += f"        return {field};\n    }}\n"

        # Setter
        class_template += f"\n    public void set{field.capitalize()}({field_type} {field}) {{\n"
        class_template += f"        this.{field} = {field};\n    }}\n"

    class_template += "}"
    return class_template


# Function to generate the Repository interface
def generate_repository_interface(entity):
    return f"package repository;\n\nimport org.springframework.data.jpa.repository.JpaRepository;\n" \
           f"import model.{entity};\n\npublic interface {entity}Repository extends JpaRepository<{entity}, Long> " + "{\n}"


# Function to generate the Service class
def generate_service_class(entity, fields):
    service_template = f"package service;\n\nimport model.{entity};\nimport repository.{entity}Repository;\n" \
                       f"import org.springframework.beans.factory.annotation.Autowired;\nimport org.springframework.http.ResponseEntity;\nimport org.springframework.stereotype.Service;\n" \
                       f"import java.util.Optional;\nimport java.util.List;\n\n@Service\npublic class {entity}Service " + "{\n" \
                                                                                              f"    @Autowired\n    private {entity}Repository {entity.lower()}Repository;\n\n" \
                                                                                              f"    public List<{entity}> getAll() {{\n        return {entity.lower()}Repository.findAll();\n    }}\n\n" \
                                                                                              f"    public {entity} getById(Long id) {{\n        return {entity.lower()}Repository.findById(id).orElse(null);\n    }}\n\n" \
                                                                                              f"    public ResponseEntity<{entity}> updateById(Long id, {entity} updated{entity}) {{\n" \
                                                                                              f"        Optional<{entity}> existing{entity} = {entity.lower()}Repository.findById(id);\n" \
                                                                                              f"        if (existing{entity}.isPresent()) {{\n" \
                                                                                              f"            {entity} {entity.lower()} = existing{entity}.get();\n"

    # Generate the setter calls for each field dynamically
    for field in fields:
        if field.lower() != "id":
            capitalized_field = field.capitalize()
            service_template += f"            {entity.lower()}.set{capitalized_field}(updated{entity}.get{capitalized_field}());\n"

    service_template += f"            {entity} saved{entity} = {entity.lower()}Repository.save({entity.lower()});\n" \
                        f"            return ResponseEntity.ok(saved{entity});\n" \
                        f"        }} else {{\n" \
                        f"            return ResponseEntity.notFound().build();\n" \
                        f"        }}\n" \
                        f"    }}\n\n" \
                        f"    public {entity} save({entity} {entity.lower()}) {{\n        return {entity.lower()}Repository.save({entity.lower()});\n    }}\n\n" \
                        f"    public void delete(Long id) {{\n        {entity.lower()}Repository.deleteById(id);\n    }}\n}}"
    return service_template



# Function to generate the Controller class
def generate_controller_class(entity):
    controller_template = f"package controller;\n\nimport model.{entity};\nimport service.{entity}Service;\n" \
                          f"import org.springframework.beans.factory.annotation.Autowired;\n" \
                          f"import org.springframework.web.bind.annotation.*;\n\n" \
                          f"import java.util.*;\n\n@RestController\n@RequestMapping(\"/{entity.lower()}\")\n" \
                          f"public class {entity}Controller " + "{\n\n" \
                                                                f"    @Autowired\n    private {entity}Service {entity.lower()}Service;\n\n" \
                                                                f"    @GetMapping\n    public List<{entity}> getAll() {{\n" \
                                                                f"        return {entity.lower()}Service.getAll();\n    }}\n\n" \
                                                                f"    @GetMapping(\"/{{id}}\")\n    public {entity} getById(@PathVariable Long id) {{\n" \
                                                                f"        return {entity.lower()}Service.getById(id);\n    }}\n\n" \
                                                                f"    @PostMapping\n    public {entity} create(@RequestBody {entity} {entity.lower()}) {{\n" \
                                                                f"        return {entity.lower()}Service.save({entity.lower()});\n    }}\n\n" \
                                                                f"    @PutMapping(\"/{{id}}\")\n      public ResponseEntity<{entity}> update(@PathVariable Long id,@RequestBody {entity} {entity.lower()}) {{\n" \
                                                                f"        return {entity.lower()}Service.updateById(id, {entity.lower()});\n    }}\n\n" \
                                                                f"    @DeleteMapping(\"/{{id}}\")\n    public void delete(@PathVariable Long id) {{\n" \
                                                                f"        {entity.lower()}Service.delete(id);\n    }}\n}}"
    return controller_template


# Main function to generate all the files
def generate_java_classes(json_data):
    entity = json_data["entity"]
    fields = json_data["fields"]
    project_name = json_data["project_name"]
    base_path = json_data["base_path"]  # Get base path from JSON

    # Create folder structure with base path and project name
    project_path = create_directory_structure(base_path, project_name)

    # Generate model
    model_class = generate_model_class(entity, fields)
    with open(os.path.join(project_path, "model", f"{entity}.java"), "w") as f:
        f.write(model_class)
        print(f"{entity}.java Model class created.")

    # Generate repository
    repository_class = generate_repository_interface(entity)
    with open(os.path.join(project_path, "repository", f"{entity}Repository.java"), "w") as f:
        f.write(repository_class)
        print(f"{entity}Repository.java Repository interface created.")

    # Generate service
    service_class = generate_service_class(entity,fields)
    with open(os.path.join(project_path, "service", f"{entity}Service.java"), "w") as f:
        f.write(service_class)
        print(f"{entity}Service.java Service class created.")

    # Generate controller
    controller_class = generate_controller_class(entity)
    with open(os.path.join(project_path, "controller", f"{entity}Controller.java"), "w") as f:
        f.write(controller_class)
        print(f"{entity}Controller.java Controller class created.")


# Flask route to handle JSON input and generate Java classes
@app.route('/generate', methods=['POST'])
def generate_code():
    try:
        # Get JSON input from the request
        data = request.get_json()

        # Basic validation for required fields in the request
        required_fields = ['entity', 'fields', 'project_name', 'base_path']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify(
                {"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

        # Check if 'id' is in the 'fields' object
        if 'id' not in data['fields']:
            return jsonify(
                {"error": "'id' is a mandatory field and must be included in 'fields'"}), 400

        # Call the function to generate Java classes
        generate_java_classes(data)

        return jsonify({"status": "Java files generated successfully!"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500



# Start Flask app
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
