import Ajv from "ajv";
const ajv = new Ajv();

const nextStepsSchema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "condition": {
            "type": "string",
            "enum": ["AND", "OR"]
        },
        "then": {
            "type": "integer",
        },
        "rules": {
            "type": "array",
            "items": {
                "oneOf": [
                    {
                        "type": "object",
                        "properties": {
                            "field": { "type": "string" },
                            "operator": {
                                "type": "string",
                                "enum": ["eq", "gt", "lt", "gte", "lte", "neq"]
                            },
                            "value": {}
                        },
                        "required": ["field", "operator", "value"],
                        "additionalProperties": false
                    },
                    {
                        "$ref": "#"
                    }
                ]
            }
        }
    },
    "required": ["condition", "rules"],
    "additionalProperties": false
};

export const nextStepsSchemaValidator = ajv.compile(nextStepsSchema);