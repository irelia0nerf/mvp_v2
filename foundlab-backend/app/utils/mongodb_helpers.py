from bson import ObjectId


class PyObjectId(str):
    """
    Custom type for validating MongoDB ObjectIds in Pydantic models.
    """

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(v)
